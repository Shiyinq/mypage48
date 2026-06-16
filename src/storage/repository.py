import asyncio
import io
from datetime import timedelta
from typing import Optional

from minio import Minio
from minio.error import S3Error
from minio.lifecycleconfig import Expiration, Filter, LifecycleConfig, Rule

from src.config import Settings
from src.logging_config import create_logger
from src.utils import resolve_minio_public_url

logger = create_logger("storage_repository", __name__)


class StorageRepository:
    """Low-level S3-compatible client wrapper (MinIO/R2)."""

    def __init__(self, config: Settings):
        self.config = config
        self._client: Optional[Minio] = None
        self._bucket_ensured = False

    @property
    def client(self) -> Minio:
        """Lazy initialization of S3 client."""
        if self._client is None:
            # Clean endpoint: strip protocol and trailing slashes
            # Minio library expects hostname:port and handles protocol via 'secure' flag
            endpoint = self.config.storage_endpoint
            endpoint = (
                endpoint.replace("https://", "").replace("http://", "").strip("/")
            )

            self._client = Minio(
                endpoint,
                access_key=self.config.storage_access_key,
                secret_key=self.config.storage_secret_key,
                secure=self.config.storage_secure,
            )
        return self._client

    async def _ensure_bucket(self) -> None:
        """Ensure the bucket exists and set lifecycle rules (mainly for local MinIO)."""
        if self._bucket_ensured:
            return

        # For R2/Cloudflare, we typically manage buckets and lifecycle via Dashboard
        # and API tokens might not have permission to list/check buckets.
        if self.config.storage_provider in ["r2", "cloudflare"]:
            self._bucket_ensured = True
            return

        try:

            def _ensure():
                if not self.client.bucket_exists(self.config.storage_bucket):
                    self.client.make_bucket(self.config.storage_bucket)
                    logger.info(f"Created bucket: {self.config.storage_bucket}")

                # Set lifecycle rules for cache/external/
                lifecycle_config = LifecycleConfig(
                    [
                        Rule(
                            status="Enabled",
                            rule_filter=Filter(prefix="cache/external/"),
                            rule_id="expire_external_cache",
                            expiration=Expiration(days=7),
                        )
                    ]
                )
                self.client.set_bucket_lifecycle(
                    self.config.storage_bucket, lifecycle_config
                )

            await asyncio.to_thread(_ensure)
            self._bucket_ensured = True
        except S3Error as e:
            logger.error(f"Failed to ensure bucket or set lifecycle: {e}")
            # Don't crash if lifecycle fails (might be unsupported by provider)
            self._bucket_ensured = True

    async def upload_file(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "image/jpeg",
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload file to storage and return the object name."""
        await self._ensure_bucket()

        try:
            file_stream = io.BytesIO(data)
            file_size = len(data)

            def _upload():
                self.client.put_object(
                    self.config.storage_bucket,
                    object_name,
                    file_stream,
                    file_size,
                    content_type=content_type,
                    metadata=metadata,
                )

            await asyncio.to_thread(_upload)
            logger.info(f"Uploaded file: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """Generate presigned URL for direct object access."""
        await self._ensure_bucket()

        try:

            def _get_url():
                return self.client.presigned_get_object(
                    self.config.storage_bucket,
                    object_name,
                    expires=timedelta(seconds=expires),
                )

            url = await asyncio.to_thread(_get_url)

            return resolve_minio_public_url(url)
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    async def delete_file(self, object_name: str) -> bool:
        """Delete file from storage."""
        await self._ensure_bucket()
        object_name = object_name.lstrip("/")

        try:

            def _delete():
                self.client.remove_object(self.config.storage_bucket, object_name)

            await asyncio.to_thread(_delete)
            logger.info(f"Deleted file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file {object_name}: {e}")
            raise

    async def file_exists(self, object_name: str) -> bool:
        """Check if file exists in storage."""
        await self._ensure_bucket()
        object_name = object_name.lstrip("/")

        try:

            def _stat():
                self.client.stat_object(self.config.storage_bucket, object_name)

            await asyncio.to_thread(_stat)
            return True
        except S3Error:
            return False

    async def get_metadata(self, object_name: str) -> Optional[dict]:
        """Get object metadata from storage."""
        await self._ensure_bucket()
        try:

            def _stat():
                return self.client.stat_object(self.config.storage_bucket, object_name)

            stat = await asyncio.to_thread(_stat)
            return stat.metadata
        except S3Error:
            return None
        except Exception as e:
            logger.error(f"Error getting metadata for {object_name}: {e}")
            return None

    async def check_connection(self) -> bool:
        """Check storage connection."""
        try:

            def _check():
                return self.client.bucket_exists(self.config.storage_bucket)

            return await asyncio.to_thread(_check)
        except Exception:
            return False

    async def get_file(self, object_name: str) -> Optional[bytes]:
        """Get file content from storage."""
        await self._ensure_bucket()
        try:

            def _get():
                response = self.client.get_object(
                    self.config.storage_bucket, object_name
                )
                return response.read()

            return await asyncio.to_thread(_get)
        except S3Error as e:
            logger.error(f"Failed to get file: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file: {e}")
            return None

    async def get_file_with_metadata(
        self, object_name: str
    ) -> tuple[Optional[bytes], Optional[str]]:
        """Get file content and content type from storage."""
        await self._ensure_bucket()
        try:

            def _get_meta():
                stat = self.client.stat_object(self.config.storage_bucket, object_name)
                response = self.client.get_object(
                    self.config.storage_bucket, object_name
                )
                return response.read(), stat.content_type

            return await asyncio.to_thread(_get_meta)
        except S3Error as e:
            if e.code != "NoSuchKey":
                logger.error(f"Failed to get file with metadata: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error getting file with metadata: {e}")
            return None, None

    async def get_file_stream_with_metadata(
        self, object_name: str
    ) -> tuple[Optional[any], Optional[str]]:
        """Get file stream and content type from storage."""
        await self._ensure_bucket()
        try:

            def _get_stream():
                stat = self.client.stat_object(self.config.storage_bucket, object_name)
                response = self.client.get_object(
                    self.config.storage_bucket, object_name
                )
                return response, stat.content_type

            return await asyncio.to_thread(_get_stream)
        except S3Error as e:
            if e.code != "NoSuchKey":
                logger.error(f"Failed to get file stream with metadata: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error getting file stream with metadata: {e}")
            return None, None

    async def get_file_stream(self, object_name: str):
        """Get file stream from storage."""
        await self._ensure_bucket()
        try:

            def _get():
                return self.client.get_object(self.config.storage_bucket, object_name)

            return await asyncio.to_thread(_get)
        except S3Error as e:
            logger.error(f"Failed to get file stream: {e}")
            return None

    async def copy_file(self, source_path: str, destination_path: str) -> bool:
        """Copy file from one path to another within the same bucket."""
        await self._ensure_bucket()

        # Ensure paths don't have leading slashes
        source_path = source_path.lstrip("/")
        destination_path = destination_path.lstrip("/")

        try:
            from minio.commonconfig import CopySource

            def _copy():
                self.client.copy_object(
                    self.config.storage_bucket,
                    destination_path,
                    CopySource(self.config.storage_bucket, source_path),
                )

            await asyncio.to_thread(_copy)
            logger.info(f"Successfully copied {source_path} to {destination_path}")
            return True
        except S3Error as e:
            logger.error(
                f"S3 Error copying file from {source_path} to {destination_path}: {e}"
            )
            return False
        except Exception as e:
            logger.error(f"Unexpected error copying file: {str(e)}")
            return False
