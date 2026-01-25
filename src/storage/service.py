import base64
import re
import uuid
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.memories.schemas import MemoryItem, TopTwoShotResponse
    from src.tickets.schemas import TicketResponse
    from src.users.schemas import PublicUserResponse, ProfileFullResponse
    from src.dashboard.schemas import DashboardStatsResponse

from minio.error import S3Error

from src.config import Settings
from src.logging_config import create_logger
from src.storage.exceptions import (
    ImageNotFoundError,
    ImageUploadError,
    InvalidCategoryError,
    PresignedUrlError,
    StorageConnectionError,
)
from src.storage.repository import StorageRepository
from src.storage.schemas import ImageCategory, ImageUploadResponse, PresignedUrlResponse

logger = create_logger("storage_service", __name__)

VALID_CATEGORIES = {"ticket", "twoshot", "avatar"}

# Regex to detect base64 data URL
BASE64_PATTERN = re.compile(r"^data:image/(\w+);base64,(.+)$", re.DOTALL)


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

            # Generate presigned URL for immediate use
            url = self.repository.get_presigned_url(filename)

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

            url = self.repository.get_presigned_url(filename, expires)
            return PresignedUrlResponse(url=url, expires_in=expires)
        except S3Error as e:
            logger.error(f"MinIO error getting presigned URL: {e}")
            raise PresignedUrlError()
        except ImageNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting presigned URL: {e}")
            raise PresignedUrlError()

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

    def resolve_url(self, value: Optional[str]) -> Optional[str]:
        """
        Fast resolve of image value to URL without existence check.
        Used for list views where performance matters.
        """
        if not value:
            return None

        # Check for base64
        if value.startswith("data:image/"):
            return value

        # Check for storage filename
        # Storage filenames contain / but don't start with data: or http
        if "/" in value and not value.startswith("http"):
            try:
                # Direct call to repository without file_exists check
                return self.repository.get_presigned_url(value)
            except Exception:
                return None

        return value

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
