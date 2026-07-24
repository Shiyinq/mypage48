import asyncio
import base64
import hashlib
import hmac
import os
import re
import time
import uuid
from email.header import decode_header
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import quote

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
    r"!\[(.*?)\]\(((journal|ticket|twoshot|avatar|member|setlist)\/[^)]+)\)"
)


class StorageService:
    """Service layer for storage operations."""

    MAX_IMAGE_DIMENSION = 2000
    MEDIUM_IMAGE_DIMENSION = 1000
    SMALL_IMAGE_DIMENSION = 500
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

    def _generate_filename(
        self, user_id: str, category: str, content_type: str, slug: Optional[str] = None
    ) -> str:
        """Generate unique filename for storage."""
        # We now standardize on webp for all uploads via the upload API
        extension = "webp"

        if (category == "member" or category == "setlist") and slug:
            # Sanitize slug: lowercase, replace spaces with underscore
            # Keep other characters
            sanitized_slug = slug.lower().strip().replace(" ", "_")
            folder = "jkt48-member" if category == "member" else "setlists"
            return f"media/{folder}/{sanitized_slug}.{extension}"

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

    async def upload_image(
        self,
        user_id: str,
        base64_image: str,
        category: ImageCategory,
        slug: Optional[str] = None,
    ) -> ImageUploadResponse:
        """Upload base64 image to storage."""
        if category not in VALID_CATEGORIES:
            raise InvalidCategoryError()

        try:
            original_bytes, _ = self._parse_base64_image(base64_image)

            with Image.open(BytesIO(original_bytes)) as img:
                blurHash = self._generate_blurhash_from_image(img)
                filename = self._generate_filename(
                    user_id, category, "image/webp", slug
                )

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

                # Generate and upload variants
                await self._generate_and_upload_variants(img, filename)

            content_type = "image/webp"
            metadata = {"blurHash": blurHash} if blurHash else None
            await self.repository.upload_file(
                webp_bytes, filename, content_type, metadata=metadata
            )

            variants = await self.resolve_image_variants(filename)

            return ImageUploadResponse(
                filename=filename,
                url=variants["url"],
                url_medium=variants["url_medium"],
                url_small=variants["url_small"],
                blurHash=blurHash,
            )
        except S3Error as e:
            logger.error(f"MinIO error during upload: {e}")
            raise StorageConnectionError()
        except (ImageUploadError, InvalidCategoryError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during upload: {e}")
            raise ImageUploadError()

    async def get_presigned_url(
        self,
        filename: str,
        expires: int = 3600,
    ) -> PresignedUrlResponse:
        """Get presigned URL for a stored file."""
        try:
            if not await self.repository.file_exists(filename):
                raise ImageNotFoundError()

            url = await self.resolve_url(filename)
            return PresignedUrlResponse(url=url, expires_in=expires)
        except S3Error as e:
            logger.error(f"MinIO error getting presigned URL: {e}")
            raise PresignedUrlError()
        except ImageNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error getting presigned URL: {e}")
            raise PresignedUrlError()

    async def get_bulk_presigned_urls(
        self,
        filenames: list[str],
        expires: int = 3600,
    ) -> BatchPresignedUrlResponse:
        """Get presigned URLs for multiple files."""
        urls = {}
        for filename in filenames:
            try:
                # Use our proxy resolve for bulk urls as well
                url = await self.resolve_url(filename)
                urls[filename] = url
            except Exception as e:
                logger.error(f"Error getting presigned URL for {filename}: {e}")
                urls[filename] = ""

        return BatchPresignedUrlResponse(urls=urls, expires_in=expires)

    async def delete_image(self, filename: str) -> bool:
        """Delete image and its variants from storage."""
        if not filename:
            return False

        # Don't try to delete external URLs or base64
        if filename.startswith("http") or filename.startswith("data:"):
            logger.debug(f"Skipping deletion for non-internal path: {filename[:50]}...")
            return False

        path = filename.lstrip("/")

        try:
            # Main file
            exists = await self.repository.file_exists(path)
            if not exists:
                logger.warning(f"File not found for deletion: {path}")
                # We return True because the goal (file not being there) is achieved
                return True

            # Delete original and variants (best effort for variants)
            variant_paths = [
                path,
                self._get_variant_path(path, "medium"),
                self._get_variant_path(path, "small"),
            ]

            tasks = []
            for p in variant_paths:
                tasks.append(self.repository.delete_file(p))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check if original file was deleted (first item in tasks)
            if isinstance(results[0], Exception):
                logger.error(f"Failed to delete original file {path}: {results[0]}")
                return False

            return True
        except Exception as e:
            logger.exception(f"Unexpected error during delete: {e}")
            return False

    async def rename_image(
        self, old_path: str, new_slug: str, category: str, user_id: str = "admin"
    ) -> str:
        """
        Rename (Move) image and its variants to a new slug.
        Returns the new path.
        """
        if not old_path or not new_slug:
            return old_path

        # Don't rename if it's an external URL
        if old_path.startswith("http") or "data:image" in old_path:
            return old_path

        new_path = self._generate_filename(user_id, category, "image/webp", new_slug)
        if old_path == new_path:
            return old_path

        # Define suffixes for variants (Main file first)
        suffixes = ["", "medium", "small"]

        async def move_single(suffix: str) -> bool:
            # Helper to move a single variant
            o_path = self._get_variant_path(old_path, suffix) if suffix else old_path
            n_path = self._get_variant_path(new_path, suffix) if suffix else new_path

            try:
                if await self.repository.file_exists(o_path):
                    if await self.repository.copy_file(o_path, n_path):
                        await self.repository.delete_file(o_path)
                        logger.debug(
                            f"Successfully moved variant [{suffix if suffix else 'original'}]"
                        )
                        return True
                else:
                    logger.debug(
                        f"Variant [{suffix if suffix else 'original'}] not found at {o_path}, skipping."
                    )
                return False
            except Exception as e:
                logger.error(f"Failed to move variant {suffix} from {o_path}: {e}")
                return False

        # Move all variants in parallel
        results = await asyncio.gather(
            *(move_single(s) for s in suffixes), return_exceptions=True
        )

        # Only return new_path if the main file (index 0) was successfully moved
        if results and results[0] is True:
            logger.info(f"SUCCESS: Renamed image from [{old_path}] to [{new_path}]")
            return new_path

        logger.warning(
            f"FAILED: Could not rename image from [{old_path}] to [{new_path}]. Keeping old path."
        )
        return old_path

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

    async def resolve_url(
        self, value: Optional[str], variant: Optional[str] = None
    ) -> Optional[str]:
        """
        Fast resolve of image value to URL.
        If STORAGE_USE_PRESIGNED is True, generates a direct S3/R2 presigned URL.
        Otherwise, returns a signed proxy URL.
        Optional variant: 'medium' or 'small'.
        """
        if not value:
            return None

        # Check for base64 or full URL
        if value.startswith("data:") or value.startswith("http"):
            return value

        path = value.lstrip("/")

        # Apply variant if requested
        if variant in ["medium", "small"]:
            path = self._get_variant_path(path, variant)

        # Strategy 1: Direct Presigned URL (Best performance, low BE load)
        if self.config.storage_use_presigned:
            try:
                return await self.repository.get_presigned_url(path)
            except Exception as e:
                logger.error(f"Failed to generate direct presigned URL for {path}: {e}")
                # Fallback to proxy if presign fails

        # Strategy 2: Proxy URL (Secure, handles signature mismatch in local dev)
        signature, expires = self._create_signed_params(path)
        encoded_path = quote(path)
        return f"{self.config.api_base_url}/storage/m/{encoded_path}?expires={expires}&signature={signature}"

    async def resolve_image_variants(
        self, path: Optional[str], default_blur_hash: Optional[str] = None
    ) -> dict[str, Optional[str]]:
        """
        Resolve all image variants (Original, Medium, Small) for a given path.
        Returns a dict with 'url', 'url_medium', 'url_small', and 'blurHash'.
        """
        if default_blur_hash:
            results = await asyncio.gather(
                self.resolve_url(path),
                self.resolve_url(path, variant="medium"),
                self.resolve_url(path, variant="small"),
            )
            url, url_medium, url_small = results
            return {
                "url": url,
                "url_medium": url_medium,
                "url_small": url_small,
                "blurHash": default_blur_hash,
            }

        # Gather URLs and metadata
        results = await asyncio.gather(
            self.resolve_url(path),
            self.resolve_url(path, variant="medium"),
            self.resolve_url(path, variant="small"),
            self.repository.get_metadata(path.lstrip("/") if path else None),
        )

        url, url_medium, url_small, metadata = results

        blurHash = None
        if metadata:
            # MinIO/S3 metadata is usually prefixed, but the library might normalize it.
            # We check both common patterns.
            raw_blurHash = metadata.get("x-amz-meta-blurhash") or metadata.get(
                "blurhash"
            )

            if raw_blurHash:
                try:
                    # Handle RFC 2047 encoding (MIME encoded-word)
                    # Library minio might encode metadata containing special characters
                    decoded_parts = decode_header(raw_blurHash)
                    blurHash = ""
                    for content, encoding in decoded_parts:
                        if isinstance(content, bytes):
                            blurHash += content.decode(encoding or "utf-8")
                        else:
                            blurHash += content
                except Exception as e:
                    logger.warning(f"Failed to decode blurHash metadata: {e}")
                    blurHash = raw_blurHash  # Fallback to raw if decoding fails

        return {
            "url": url,
            "url_medium": url_medium,
            "url_small": url_small,
            "blurHash": blurHash,
        }

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
        if not await self.repository.file_exists(cache_key):
            # Not in cache, fetch and upload
            try:
                await self._cache_external_media(path)
            except Exception as e:
                logger.error(f"Failed to JIT cache external media {path}: {e}")
                # Fallback to backend proxy if cache fails
                return f"{self.config.api_base_url}/storage/external/{path}"

        # Now it's guaranteed to be in R2, resolve via standard logic
        return await self.resolve_url(cache_key)

    async def resolve_external_media(self, value: Optional[str]) -> dict:
        """
        New specialized resolve that returns URL variants and BlurHash.
        """
        if not value:
            return {
                "url": None,
                "url_medium": None,
                "url_small": None,
                "blurHash": None,
            }

        # Check if it's already a full URL or base64
        if value.startswith("data:") or value.startswith("http"):
            # If it's a jkt48 storage URL, treat it as a path
            if "jkt48.com/api/v1/storages/" in value:
                value = value.split("jkt48.com/api/v1/storages/")[1]
            else:
                return {
                    "url": value,
                    "url_medium": None,
                    "url_small": None,
                    "blurHash": None,
                }

        path = value.lstrip("/")
        cache_key = f"cache/external/{path}"
        blurHash = None

        if not await self.repository.file_exists(cache_key):
            try:
                blurHash = await self._cache_external_media(path)
            except Exception as e:
                logger.error(f"Failed to JIT cache external media {path}: {e}")
                # Fallback to backend proxy if cache fails
                return {
                    "url": f"{self.config.api_base_url}/storage/external/{path}",
                    "url_medium": None,
                    "url_small": None,
                    "blurHash": None,
                }

        # Guaranteed to be in R2 (either previously or just now)
        variants = await self.resolve_image_variants(cache_key)

        # If we just cached it, blurHash is from _cache_external_media.
        # Otherwise, it will be in variants["blurHash"] from metadata.
        return {**variants, "blurHash": blurHash or variants.get("blurHash")}

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
                        img.thumbnail(
                            (self.MAX_IMAGE_DIMENSION, self.MAX_IMAGE_DIMENSION)
                        )

                    # Save as WebP (stripping EXIF by not passing it)
                    img.save(output, format="WEBP", quality=self.WEBP_QUALITY)
                    webp_data = output.getvalue()
                    content_type = "image/webp"

                    # Generate and upload variants
                    await self._generate_and_upload_variants(img, cache_key)

                    metadata = {"blurHash": blurHash} if blurHash else None
                    await self.repository.upload_file(
                        webp_data, cache_key, content_type, metadata=metadata
                    )
                    logger.info(f"Successfully cached {path} to R2 as WebP")
                    return blurHash
            except Exception as e:
                logger.error(f"Failed to process and upload {path} to R2: {e}")
        return None

    async def resolve_markdown_images(self, content: Optional[str]) -> Optional[str]:
        """
        Find internal storage paths in markdown and replace with resolved URLs.
        """
        if not content:
            return content

        matches = list(MARKDOWN_IMAGE_PATTERN.finditer(content))
        if not matches:
            return content

        paths = [m.group(2) for m in matches]
        urls = await asyncio.gather(
            *(self.resolve_url(path) for path in paths), return_exceptions=True
        )

        result = content
        # we iterate backward so replacements don't mess up earlier indices
        for match, url_obj in reversed(list(zip(matches, urls))):
            alt_text = match.group(1)
            match.group(0)
            if isinstance(url_obj, str):
                proxy_url = url_obj
                result = (
                    result[: match.start()]
                    + f"![{alt_text}]({proxy_url})"
                    + result[match.end() :]
                )
        return result

    async def resolve_dashboard_stats(
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
            variants = await self.resolve_image_variants(
                stats_dict["two_shot"]["top_2_shot"]["image"]
            )
            stats_dict["two_shot"]["top_2_shot"]["image"] = variants["url"]
            stats_dict["two_shot"]["top_2_shot"]["image_medium"] = variants[
                "url_medium"
            ]
            stats_dict["two_shot"]["top_2_shot"]["image_small"] = variants["url_small"]
            stats_dict["two_shot"]["top_2_shot"]["blurHash"] = variants.get(
                "blurHash"
            ) or stats_dict["two_shot"]["top_2_shot"].get("blurHash")

        # 2. Resolve Extremes (First/Last) in Two Shot
        if stats_dict.get("two_shot") and stats_dict["two_shot"].get("extremes"):
            extremes = stats_dict["two_shot"]["extremes"]
            for key in ["first", "last"]:
                if extremes.get(key) and extremes[key].get("image"):
                    variants = await self.resolve_image_variants(extremes[key]["image"])
                    stats_dict["two_shot"]["extremes"][key]["image"] = variants["url"]
                    stats_dict["two_shot"]["extremes"][key]["image_medium"] = variants[
                        "url_medium"
                    ]
                    stats_dict["two_shot"]["extremes"][key]["image_small"] = variants[
                        "url_small"
                    ]
                    stats_dict["two_shot"]["extremes"][key]["blurHash"] = variants.get(
                        "blurHash"
                    ) or stats_dict["two_shot"]["extremes"][key].get("blurHash")

        # 3. Resolve Top Show image
        if (
            stats_dict.get("theater")
            and stats_dict["theater"].get("top_show")
            and stats_dict["theater"]["top_show"].get("image")
        ):
            variants = await self.resolve_image_variants(
                stats_dict["theater"]["top_show"]["image"]
            )
            stats_dict["theater"]["top_show"]["image"] = variants["url"]
            stats_dict["theater"]["top_show"]["image_medium"] = variants["url_medium"]
            stats_dict["theater"]["top_show"]["image_small"] = variants["url_small"]
            stats_dict["theater"]["top_show"]["blurHash"] = variants.get(
                "blurHash"
            ) or stats_dict["theater"]["top_show"].get("blurHash")

        # 4. Resolve Theater Extremes
        if stats_dict.get("theater") and stats_dict["theater"].get("extremes"):
            extremes = stats_dict["theater"]["extremes"]
            for key in ["first", "last"]:
                if extremes.get(key) and extremes[key].get("image"):
                    variants = await self.resolve_image_variants(extremes[key]["image"])
                    stats_dict["theater"]["extremes"][key]["image"] = variants["url"]
                    stats_dict["theater"]["extremes"][key]["image_medium"] = variants[
                        "url_medium"
                    ]
                    stats_dict["theater"]["extremes"][key]["image_small"] = variants[
                        "url_small"
                    ]
                    stats_dict["theater"]["extremes"][key]["blurHash"] = variants.get(
                        "blurHash"
                    ) or stats_dict["theater"]["extremes"][key].get("blurHash")

        return type(stats)(**stats_dict)

    async def resolve_ticket_images(self, ticket: Any) -> Any:
        """
        Resolve all potential images in a ticket (main image and 2-shot).
        Updates the ticket object in-place.
        """
        if not ticket:
            return ticket

        # Main image
        if hasattr(ticket, "imageUrl") and ticket.imageUrl:
            variants = await self.resolve_image_variants(ticket.imageUrl)
            ticket.imageUrl = variants["url"]
            ticket.imageUrl_medium = variants["url_medium"]
            ticket.imageUrl_small = variants["url_small"]

        # 2-Shot image
        if (
            hasattr(ticket, "two_shot")
            and ticket.two_shot
            and hasattr(ticket.two_shot, "imageUrl")
            and ticket.two_shot.imageUrl
        ):
            variants = await self.resolve_image_variants(ticket.two_shot.imageUrl)
            ticket.two_shot.imageUrl = variants["url"]
            ticket.two_shot.imageUrl_medium = variants["url_medium"]
            ticket.two_shot.imageUrl_small = variants["url_small"]

        return ticket

    def _get_variant_path(self, path: str, variant: str) -> str:
        """Helper to get path for a variant."""
        if not path:
            return path
        name, ext = os.path.splitext(path)
        return f"{name}_{variant}{ext}"

    async def _generate_and_upload_variants(
        self, img: Image.Image, base_path: str
    ) -> None:
        """Helper to generate and upload medium/small variants."""
        variants = {
            "medium": self.MEDIUM_IMAGE_DIMENSION,
            "small": self.SMALL_IMAGE_DIMENSION,
        }

        for suffix, dimension in variants.items():
            try:
                variant_path = self._get_variant_path(base_path, suffix)

                # We work on a copy to avoid shrinking the original in the loop
                temp_img = img.copy()

                # Check if we need to resize
                if max(temp_img.width, temp_img.height) > dimension:
                    temp_img.thumbnail((dimension, dimension))

                output = BytesIO()
                temp_img.save(output, format="WEBP", quality=self.WEBP_QUALITY)
                variant_bytes = output.getvalue()

                await self.repository.upload_file(
                    variant_bytes, variant_path, "image/webp"
                )
                logger.debug(f"Generated and uploaded variant: {variant_path}")
            except Exception as e:
                logger.error(
                    f"Failed to generate {suffix} variant for {base_path}: {e}"
                )

    async def process_and_upload_webp(
        self, image_bytes: bytes, path: str
    ) -> Optional[str]:
        """Convert raw image bytes to WebP, generate blurhash, upload.

        Returns blurHash if successful.
        """
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                blurHash = self._generate_blurhash_from_image(img)

                output = BytesIO()
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

                if max(img.width, img.height) > self.MAX_IMAGE_DIMENSION:
                    img.thumbnail((self.MAX_IMAGE_DIMENSION, self.MAX_IMAGE_DIMENSION))

                img.save(output, format="WEBP", quality=self.WEBP_QUALITY)
                webp_bytes = output.getvalue()

                metadata = {"blurHash": blurHash} if blurHash else None
                await self.repository.upload_file(
                    webp_bytes, path, "image/webp", metadata=metadata
                )
                return blurHash
        except Exception as e:
            logger.error(f"Failed to process and upload WebP to {path}: {e}")
            return None

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
            stream, content_type = await self.repository.get_file_stream_with_metadata(
                path
            )
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
            stream, content_type = await self.repository.get_file_stream_with_metadata(
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
            stream, content_type = await self.repository.get_file_stream_with_metadata(
                cache_key
            )
            return stream, content_type or "image/jpeg", 200

        return [b"Not Found"], "text/plain", 404
