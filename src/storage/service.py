import base64
import hashlib
import hmac
import re
import time
import uuid
from typing import TYPE_CHECKING, Optional

import httpx

if TYPE_CHECKING:
    from src.memories.schemas import MemoryItem, TopTwoShotResponse
    from src.tickets.schemas import TicketResponse
    from src.users.schemas import PublicUserResponse, ProfileFullResponse
    from src.dashboard.schemas import DashboardStatsResponse

from minio.error import S3Error

from src.config import Settings
from src.logging_config import create_logger
from src.storage.constants import VALID_CATEGORIES
from src.storage.exceptions import (
    ImageNotFoundError,
    ImageUploadError,
    InvalidCategoryError,
    PresignedUrlError,
    StorageConnectionError,
)
from src.storage.repository import StorageRepository
from src.storage.schemas import (
    BatchPresignedUrlResponse,
    ImageCategory,
    ImageUploadResponse,
    PresignedUrlResponse,
)

logger = create_logger("storage_service", __name__)

# Regex to detect base64 data URL
BASE64_PATTERN = re.compile(r"^data:image/(\w+);base64,(.+)$", re.DOTALL)

# Regex to detect internal storage paths in markdown: ![](journal/abc.png)
MARKDOWN_IMAGE_PATTERN = re.compile(
    r"!\[(.*?)\]\(((journal|ticket|twoshot|avatar)\/[^)]+)\)"
)


class StorageService:
    """Service layer for storage operations."""

    def __init__(self, repository: StorageRepository, config: Settings):
        self.repository = repository
        self.config = config

    def _parse_base64_image(self, base64_string: str) -> tuple[bytes, str]:
        """Parse base64 image string and return bytes and content type."""
        match = BASE64_PATTERN.match(base64_string)
        if not match:
            raise ImageUploadError()

        image_format = match.group(1).lower()
        base64_data = match.group(2)

        # Map format to content type
        content_type_map = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }

        content_type = content_type_map.get(image_format, "image/jpeg")

        try:
            image_bytes = base64.b64decode(base64_data)
        except Exception:
            raise ImageUploadError()

        return image_bytes, content_type

    def _generate_filename(self, user_id: str, category: str, content_type: str) -> str:
        """Generate unique filename for storage."""
        extension_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
        }
        extension = extension_map.get(content_type, "jpg")
        unique_id = uuid.uuid4().hex[:12]
        return f"{category}/{user_id}/{unique_id}.{extension}"

    def upload_image(
        self,
        user_id: str,
        base64_image: str,
        category: ImageCategory,
    ) -> ImageUploadResponse:
        """Upload base64 image to storage."""
        if category not in VALID_CATEGORIES:
            raise InvalidCategoryError()

        try:
            image_bytes, content_type = self._parse_base64_image(base64_image)
            filename = self._generate_filename(user_id, category, content_type)

            self.repository.upload_file(image_bytes, filename, content_type)

            # Use our proxy resolve instead of direct MinIO presigned URL
            url = self.resolve_url(filename)

            return ImageUploadResponse(filename=filename, url=url)
        except S3Error as e:
            logger.error(f"MinIO error during upload: {e}")
            raise StorageConnectionError()
        except (ImageUploadError, InvalidCategoryError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during upload: {e}")
            raise ImageUploadError()

    def get_presigned_url(
        self,
        filename: str,
        expires: int = 3600,
    ) -> PresignedUrlResponse:
        """Get presigned URL for a stored file."""
        try:
            if not self.repository.file_exists(filename):
                raise ImageNotFoundError()

            url = self.resolve_url(filename)
            return PresignedUrlResponse(url=url, expires_in=expires)
        except S3Error as e:
            logger.error(f"MinIO error getting presigned URL: {e}")
            raise PresignedUrlError()
        except ImageNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting presigned URL: {e}")
            raise PresignedUrlError()

    def get_bulk_presigned_urls(
        self,
        filenames: list[str],
        expires: int = 3600,
    ) -> BatchPresignedUrlResponse:
        """Get presigned URLs for multiple files."""
        urls = {}
        for filename in filenames:
            try:
                # Use our proxy resolve for bulk urls as well
                url = self.resolve_url(filename)
                urls[filename] = url
            except Exception as e:
                logger.error(f"Error getting presigned URL for {filename}: {e}")
                urls[filename] = ""

        return BatchPresignedUrlResponse(urls=urls, expires_in=expires)

    def delete_image(self, filename: str) -> bool:
        """Delete image from storage."""
        try:
            if not self.repository.file_exists(filename):
                raise ImageNotFoundError()

            return self.repository.delete_file(filename)
        except S3Error as e:
            logger.error(f"MinIO error during delete: {e}")
            raise StorageConnectionError()
        except ImageNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during delete: {e}")
            return False

    def _generate_signature(self, path: str, expires: int) -> str:
        """
        Generate a secure HMAC signature for a path and expiration timestamp.
        Used for proxy-based presigned URLs.
        """
        message = f"{path}:{expires}"
        return hmac.new(
            self.config.secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

    def _create_signed_params(self, path: str, ttl: int = 3600) -> tuple[str, int]:
        """
        Create signature and expiration timestamp for a path.
        """
        expires = int(time.time()) + ttl
        signature = self._generate_signature(path, expires)
        return signature, expires

    def verify_signature(self, path: str, expires: str, signature: str) -> bool:
        """
        Verify if the signature is valid for the given path and has not expired.
        """
        try:
            expires_int = int(expires)
            if expires_int < int(time.time()):
                logger.warning(f"Signature expired for path: {path}")
                return False

            expected_sig = self._generate_signature(path, expires_int)
            if hmac.compare_digest(expected_sig, signature):
                return True

            logger.warning(f"Invalid signature for path: {path}")
            return False
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    def resolve_url(self, value: Optional[str]) -> Optional[str]:
        """
        Fast resolve of image value to URL without existence check.
        Automatically appends a 1-hour access signature for internal paths.
        """
        if not value:
            return None

        # Check for base64
        if value.startswith("data:image/"):
            return value

        # Check for storage filename
        # Storage filenames contain / but don't start with data: or http
        if "/" in value and not value.startswith("http"):
            path = value.lstrip("/")

            # Signature generation logic moved to _create_signed_params
            signature, expires = self._create_signed_params(path)

            return f"{self.config.api_base_url}/storage/m/{path}?expires={expires}&signature={signature}"

        return value

    def resolve_markdown_images(self, content: Optional[str]) -> Optional[str]:
        """
        Find internal storage paths in markdown and replace with proxy URLs using signatures.
        """
        if not content:
            return content

        def replace_path(match):
            alt_text = match.group(1)
            path = match.group(2)
            try:
                # Use resolve_url to get the signed proxy URL
                proxy_url = self.resolve_url(path)
                return f"![{alt_text}]({proxy_url})"
            except Exception:
                return match.group(0)

        return MARKDOWN_IMAGE_PATTERN.sub(replace_path, content)

    def resolve_ticket_images(self, ticket: "TicketResponse") -> "TicketResponse":
        """Resolve storage filenames to presigned URLs for a ticket."""
        # Using model_dump and reconstruct pattern
        ticket_dict = ticket.model_dump()

        if ticket_dict.get("imageUrl"):
            ticket_dict["imageUrl"] = self.resolve_url(ticket_dict["imageUrl"])

        if ticket_dict.get("two_shot") and ticket_dict["two_shot"].get("imageUrl"):
            ticket_dict["two_shot"]["imageUrl"] = self.resolve_url(
                ticket_dict["two_shot"]["imageUrl"]
            )

        if ticket_dict.get("notes"):
            ticket_dict["notes"] = self.resolve_markdown_images(ticket_dict["notes"])

        return type(ticket)(**ticket_dict)

    def resolve_public_user_images(
        self, user: "PublicUserResponse"
    ) -> "PublicUserResponse":
        """Resolve profile picture to presigned URL for public profile."""
        user_dict = user.model_dump()

        if user_dict.get("profilePicture"):
            user_dict["profilePicture"] = self.resolve_url(user_dict["profilePicture"])

        return type(user)(**user_dict)

    def resolve_profile_full_images(
        self, profile: "ProfileFullResponse"
    ) -> "ProfileFullResponse":
        """Resolve profile picture to presigned URL for full profile."""
        profile_dict = profile.model_dump()

        if profile_dict.get("profile") and profile_dict["profile"].get(
            "profilePicture"
        ):
            profile_dict["profile"]["profilePicture"] = self.resolve_url(
                profile_dict["profile"]["profilePicture"]
            )

        return type(profile)(**profile_dict)

    def resolve_memory_item_image(self, memory: "MemoryItem") -> "MemoryItem":
        """Resolve memory item image to presigned URL."""
        memory_dict = memory.model_dump()

        if memory_dict.get("imageUrl"):
            memory_dict["imageUrl"] = self.resolve_url(memory_dict["imageUrl"])

        return type(memory)(**memory_dict)

    def resolve_top_twoshot_images(
        self, response: "TopTwoShotResponse"
    ) -> "TopTwoShotResponse":
        """Resolve top 2-shot member images to presigned URLs."""
        response_dict = response.model_dump()

        if response_dict.get("ranking"):
            for member in response_dict["ranking"]:
                if member.get("image"):
                    member["image"] = self.resolve_url(member["image"])

        return type(response)(**response_dict)

    def resolve_dashboard_stats(
        self, stats: "DashboardStatsResponse"
    ) -> "DashboardStatsResponse":
        """Resolve images in dashboard statistics to presigned URLs."""
        # We need to construct a new dictionary or copy to mutate it
        stats_dict = stats.model_dump()

        # 1. Resolve Top 2-Shot Member
        if (
            stats_dict.get("two_shot")
            and stats_dict["two_shot"].get("top_2_shot")
            and stats_dict["two_shot"]["top_2_shot"].get("image")
        ):
            stats_dict["two_shot"]["top_2_shot"]["image"] = self.resolve_url(
                stats_dict["two_shot"]["top_2_shot"]["image"]
            )

        # 2. Resolve Extremes (First/Last) in Two Shot
        if stats_dict.get("two_shot") and stats_dict["two_shot"].get("extremes"):
            extremes = stats_dict["two_shot"]["extremes"]
            if extremes.get("first") and extremes["first"].get("image"):
                extremes["first"]["image"] = self.resolve_url(
                    extremes["first"]["image"]
                )
            if extremes.get("last") and extremes["last"].get("image"):
                extremes["last"]["image"] = self.resolve_url(extremes["last"]["image"])

        return type(stats)(**stats_dict)

    async def get_internal_media(
        self,
        path: str,
    ) -> tuple[Optional[bytes], str, int]:
        """
        Get internal media from MinIO.
        Returns (content, media_type, status_code).
        Signature verification happens at the route level.
        """
        path = path.lstrip("/")

        try:
            content, content_type = self.repository.get_file_with_metadata(path)
            if content:
                return content, content_type or "image/jpeg", 200

            return b"Not Found", "text/plain", 404
        except Exception as e:
            logger.exception(f"Error getting media {path}: {str(e)}")
            return b"Error", "text/plain", 500

    async def get_external_media(self, path: str) -> tuple[Optional[bytes], str, int]:
        """
        Get external media from cache or original source.
        Returns (content, media_type, status_code).
        """
        path = path.lstrip("/")
        cache_key = f"cache/external/{path}"

        # 1. Try cache
        try:
            content, content_type = self.repository.get_file_with_metadata(cache_key)
            if content:
                logger.info(f"Serving external media from cache: {path}")
                return content, content_type or "image/jpeg", 200
        except Exception as e:
            logger.error(f"Error checking cache for {path}: {e}")

        # 2. Fetch from source
        upstream_url = f"https://jkt48.com/api/v1/storages/{path}"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                upstream_response = await client.get(upstream_url)

            if upstream_response.status_code == 200:
                content = upstream_response.content
                content_type = upstream_response.headers.get(
                    "content-type", "image/jpeg"
                )

                # 3. Cache it
                try:
                    self.repository.upload_file(content, cache_key, content_type)
                    logger.info(f"Cached external media: {path}")
                except Exception as e:
                    logger.error(f"Failed to cache external media {path}: {e}")

                return content, content_type, 200

            # Forward other status codes as-is
            return (
                upstream_response.content,
                "text/plain",
                upstream_response.status_code,
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching external media: {path}")
            return b"Gateway Timeout", "text/plain", 504
        except Exception as e:
            logger.error(f"Error fetching external media: {e}")
            return b"Bad Gateway", "text/plain", 502
