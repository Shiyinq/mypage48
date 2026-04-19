import base64
import hashlib
import hmac
import re
import time
import uuid
from typing import TYPE_CHECKING, Optional

import httpx

if TYPE_CHECKING:
    from src.dashboard.schemas import DashboardStatsResponse

from io import BytesIO

import blurhash
from minio.error import S3Error
from PIL import Image

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

BASE64_PATTERN = re.compile(r"^data:image/(\w+);base64,(.+)$", re.DOTALL)

MARKDOWN_IMAGE_PATTERN = re.compile(
    r"!\[(.*?)\]\(((journal|ticket|twoshot|avatar)\/[^)]+)\)"
)


class StorageService:
    """Service layer for storage operations."""

    MAX_IMAGE_DIMENSION = 2000
    WEBP_QUALITY = 75

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
        # We now standardize on webp for all uploads via the upload API
        extension = "webp"
        unique_id = uuid.uuid4().hex[:12]
        return f"{category}/{user_id}/{unique_id}.{extension}"

    def _generate_blurhash_from_image(self, img: Image.Image) -> Optional[str]:
        """Generate a BlurHash for the given PIL Image object."""
        try:
            temp_img = img.copy()
            if temp_img.mode != "RGB":
                temp_img = temp_img.convert("RGB")

            temp_img.thumbnail((32, 32))

            width, height = temp_img.size
            x_components = 4
            y_components = 4 if height >= width else 3

            hash_str = blurhash.encode(
                temp_img, x_components=x_components, y_components=y_components
            )
            logger.debug(f"Generated blurhash: {hash_str}")
            return hash_str
        except Exception as e:
            logger.error(
                f"Failed to generate blurhash from image: {str(e)}", exc_info=True
            )
            return None

    def _generate_blurhash(self, image_bytes: bytes) -> Optional[str]:
        """Generate a BlurHash for the given image bytes."""
        try:
            if not image_bytes:
                logger.warning("Empty image bytes received for blurhash")
                return None

            with Image.open(BytesIO(image_bytes)) as img:
                return self._generate_blurhash_from_image(img)
        except Exception as e:
            logger.error(f"Failed to generate blurhash: {str(e)}", exc_info=True)
            return None

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
            original_bytes, _ = self._parse_base64_image(base64_image)

            with Image.open(BytesIO(original_bytes)) as img:
                blurHash = self._generate_blurhash_from_image(img)

                output = BytesIO()
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                
                # Auto-resize if too large
                if max(img.width, img.height) > self.MAX_IMAGE_DIMENSION:
                    img.thumbnail((self.MAX_IMAGE_DIMENSION, self.MAX_IMAGE_DIMENSION))
                
                # Save as WebP (stripping EXIF by not passing it)
                img.save(output, format="WEBP", quality=self.WEBP_QUALITY)
                webp_bytes = output.getvalue()
                content_type = "image/webp"

            filename = self._generate_filename(user_id, category, content_type)
            self.repository.upload_file(webp_bytes, filename, content_type)
            url = self.resolve_url(filename)

            return ImageUploadResponse(filename=filename, url=url, blurHash=blurHash)
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
        Fast resolve of image value to URL.
        If STORAGE_USE_PRESIGNED is True, generates a direct S3/R2 presigned URL.
        Otherwise, returns a signed proxy URL.
        """
        if not value:
            return None

        if value.startswith("data:image/"):
            return value

        if "/" in value and not value.startswith("http"):
            path = value.lstrip("/")

            # Strategy 1: Direct Presigned URL (Best performance, low BE load)
            if self.config.storage_use_presigned:
                try:
                    return self.repository.get_presigned_url(path)
                except Exception as e:
                    logger.error(
                        f"Failed to generate direct presigned URL for {path}: {e}"
                    )
                    # Fallback to proxy if presign fails

            # Strategy 2: Proxy URL (Secure, handles signature mismatch in local dev)
            signature, expires = self._create_signed_params(path)
            return f"{self.config.api_base_url}/storage/m/{path}?expires={expires}&signature={signature}"

        return value

    async def resolve_external_url(self, value: Optional[str]) -> Optional[str]:
        """
        Specialized resolve for external media (jkt48.com).
        Checks if the image exists in R2 cache. If not, fetches from source,
        uploads to R2, and then returns the direct R2 URL.
        """
        if not value:
            return None

        # Check if it's already a full URL or base64
        if value.startswith("data:") or value.startswith("http"):
            # If it's a jkt48 storage URL, treat it as a path
            if "jkt48.com/api/v1/storages/" in value:
                value = value.split("jkt48.com/api/v1/storages/")[1]
            else:
                return value

        path = value.lstrip("/")
        cache_key = f"cache/external/{path}"

        # Ensure it's cached in R2
        if not self.repository.file_exists(cache_key):
            # Not in cache, fetch and upload
            try:
                await self._cache_external_media(path)
            except Exception as e:
                logger.error(f"Failed to JIT cache external media {path}: {e}")
                # Fallback to backend proxy if cache fails
                return f"{self.config.api_base_url}/storage/external/{path}"

        # Now it's guaranteed to be in R2, resolve via standard logic
        return self.resolve_url(cache_key)

    async def resolve_external_media(self, value: Optional[str]) -> dict:
        """
        New specialized resolve that returns both URL and BlurHash.
        Matches the logic of resolve_external_url but returns a dict.
        """
        if not value:
            return {"url": None, "blur_hash": None}

        # Check if it's already a full URL or base64
        if value.startswith("data:") or value.startswith("http"):
            # If it's a jkt48 storage URL, treat it as a path
            if "jkt48.com/api/v1/storages/" in value:
                value = value.split("jkt48.com/api/v1/storages/")[1]
            else:
                return {"url": value, "blur_hash": None}

        path = value.lstrip("/")
        cache_key = f"cache/external/{path}"
        blurHash = None

        if not self.repository.file_exists(cache_key):
            try:
                blurHash = await self._cache_external_media(path)
            except Exception as e:
                logger.error(f"Failed to JIT cache external media {path}: {e}")
                return {
                    "url": f"{self.config.api_base_url}/storage/external/{path}",
                    "blurHash": None,
                }
        else:
            # Already in cache, but we might not have the blurHash easily available
            # We'll need a way to retrieve it. For now, we can calculate it on the fly
            # or rely on the migration script to have pre-populated it in the DB.
            # To avoid CPU spikes on GET, we'll return None and let the fallback handle it
            # if it's not already in the database record.
            pass

        return {"url": self.resolve_url(cache_key), "blurHash": blurHash}

    async def _cache_external_media(self, path: str) -> Optional[str]:
        """
        Helper to fetch from source and save to R2.
        Returns the blurHash if successful.
        """
        cache_key = f"cache/external/{path}"
        upstream_url = f"https://jkt48.com/api/v1/storages/{path}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            upstream_response = await client.get(upstream_url)

        if upstream_response.status_code == 200:
            original_content = upstream_response.content
            try:
                with Image.open(BytesIO(original_content)) as img:
                    blurHash = self._generate_blurhash_from_image(img)

                    output = BytesIO()
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGBA")
                    else:
                        img = img.convert("RGB")
                    
                    # Auto-resize if too large
                    if max(img.width, img.height) > self.MAX_IMAGE_DIMENSION:
                        img.thumbnail((self.MAX_IMAGE_DIMENSION, self.MAX_IMAGE_DIMENSION))
                    
                    # Save as WebP (stripping EXIF by not passing it)
                    img.save(output, format="WEBP", quality=self.WEBP_QUALITY)
                    webp_data = output.getvalue()
                    content_type = "image/webp"

                    self.repository.upload_file(webp_data, cache_key, content_type)
                    logger.info(f"Successfully cached {path} to R2 as WebP")
                    return blurHash
            except Exception as e:
                logger.error(f"Failed to process and upload {path} to R2: {e}")
        return None

    def resolve_markdown_images(self, content: Optional[str]) -> Optional[str]:
        """
        Find internal storage paths in markdown and replace with resolved URLs.
        """
        if not content:
            return content

        def replace_path(match):
            alt_text = match.group(1)
            path = match.group(2)
            try:
                # Use resolve_url to get the signed proxy URL or direct URL
                proxy_url = self.resolve_url(path)
                return f"![{alt_text}]({proxy_url})"
            except Exception:
                return match.group(0)

        return MARKDOWN_IMAGE_PATTERN.sub(replace_path, content)

    def resolve_dashboard_stats(
        self, stats: "DashboardStatsResponse"
    ) -> "DashboardStatsResponse":
        """Resolve images in dashboard statistics to URLs."""
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

    def resolve_ticket_images(self, ticket: any) -> any:
        """Resolve images for a ticket object."""
        if hasattr(ticket, "imageUrl") and ticket.imageUrl:
            ticket.imageUrl = self.resolve_url(ticket.imageUrl)

        if (
            hasattr(ticket, "two_shot")
            and ticket.two_shot
            and hasattr(ticket.two_shot, "imageUrl")
            and ticket.two_shot.imageUrl
        ):
            ticket.two_shot.imageUrl = self.resolve_url(ticket.two_shot.imageUrl)

        return ticket

    async def get_internal_media(
        self,
        path: str,
    ) -> tuple[Optional[any], str, int]:
        """
        Get internal media as a stream.
        Returns (stream, media_type, status_code).
        """
        path = path.lstrip("/")

        try:
            stream, content_type = self.repository.get_file_stream_with_metadata(path)
            if stream:
                return stream, content_type or "image/jpeg", 200

            return [b"Not Found"], "text/plain", 404
        except Exception as e:
            logger.exception(f"Error getting media {path}: {str(e)}")
            return [b"Error"], "text/plain", 500

    async def get_external_media(self, path: str) -> tuple[Optional[any], str, int]:
        """
        Get external media from cache or original source as a stream.
        """
        path = path.lstrip("/")
        cache_key = f"cache/external/{path}"

        try:
            stream, content_type = self.repository.get_file_stream_with_metadata(
                cache_key
            )
            if stream:
                logger.info(f"Serving external media from cache: {path}")
                return stream, content_type or "image/jpeg", 200
        except Exception as e:
            logger.error(f"Error checking cache for {path}: {e}")

        success = await self._cache_external_media(path)
        if success:
            # Serve what we just cached
            stream, content_type = self.repository.get_file_stream_with_metadata(
                cache_key
            )
            return stream, content_type or "image/jpeg", 200

        return [b"Not Found"], "text/plain", 404
