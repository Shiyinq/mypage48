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
    """Low-level MinIO client wrapper."""

    def __init__(self, config: Settings):
        self.config = config
        self._client: Optional[Minio] = None
        self._bucket_ensured = False

    @property
    def client(self) -> Minio:
        """Lazy initialization of MinIO client."""
        if self._client is None:
            self._client = Minio(
                self.config.minio_endpoint,
                access_key=self.config.minio_access_key,
                secret_key=self.config.minio_secret_key,
                secure=self.config.minio_secure,
            )
        return self._client

    def _ensure_bucket(self) -> None:
        """Ensure the bucket exists, create if not, and set lifecycle rules."""
        if self._bucket_ensured:
            return

        try:
            if not self.client.bucket_exists(self.config.minio_bucket):
                self.client.make_bucket(self.config.minio_bucket)
                logger.info(f"Created bucket: {self.config.minio_bucket}")

            # Set lifecycle rules for cache/external/
            # This will automatically delete files in this folder after 7 days
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
            self.client.set_bucket_lifecycle(self.config.minio_bucket, lifecycle_config)
            # logger.info("Set life-cycle rule for cache/external/ to 7 days") # Muted to reduce noise

            self._bucket_ensured = True
        except S3Error as e:
            logger.error(f"Failed to ensure bucket or set lifecycle: {e}")
            raise

    def upload_file(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload file to MinIO and return the object name."""
        self._ensure_bucket()

        try:
            file_stream = io.BytesIO(data)
            file_size = len(data)

            self.client.put_object(
                self.config.minio_bucket,
                object_name,
                file_stream,
                file_size,
                content_type=content_type,
            )
            logger.info(f"Uploaded file: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """Generate presigned URL for object access."""
        self._ensure_bucket()

        try:
            url = self.client.presigned_get_object(
                self.config.minio_bucket,
                object_name,
                expires=timedelta(seconds=expires),
            )

            return resolve_minio_public_url(url)
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def delete_file(self, object_name: str) -> bool:
        """Delete file from MinIO."""
        self._ensure_bucket()

        try:
            self.client.remove_object(self.config.minio_bucket, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            raise

    def file_exists(self, object_name: str) -> bool:
        """Check if file exists in MinIO."""
        self._ensure_bucket()

        try:
            self.client.stat_object(self.config.minio_bucket, object_name)
            return True
        except S3Error:
            return False

    def check_connection(self) -> bool:
        """Check MinIO connection."""
        try:
            return self.client.bucket_exists(self.config.minio_bucket)
        except Exception:
            return False

    def get_file(self, object_name: str) -> Optional[bytes]:
        """Get file content from MinIO."""
        self._ensure_bucket()
        try:
            response = self.client.get_object(self.config.minio_bucket, object_name)
            return response.read()
        except S3Error as e:
            logger.error(f"Failed to get file: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file: {e}")
            return None

    def get_file_with_metadata(
        self, object_name: str
    ) -> tuple[Optional[bytes], Optional[str]]:
        """Get file content and content type from MinIO."""
        self._ensure_bucket()
        try:
            stat = self.client.stat_object(self.config.minio_bucket, object_name)
            response = self.client.get_object(self.config.minio_bucket, object_name)
            return response.read(), stat.content_type
        except S3Error as e:
            if e.code != "NoSuchKey":
                logger.error(f"Failed to get file with metadata: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error getting file with metadata: {e}")
            return None, None

    def get_file_stream(self, object_name: str):
        """Get file stream from MinIO."""
        self._ensure_bucket()
        try:
            return self.client.get_object(self.config.minio_bucket, object_name)
        except S3Error as e:
            logger.error(f"Failed to get file stream: {e}")
            return None
