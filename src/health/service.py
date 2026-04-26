from src.database import Database
from src.health.constants import DatabaseStatus, HealthStatus
from src.health.schemas import HealthCheckResponse
from src.logging_config import create_logger
from src.storage.repository import StorageRepository

logger = create_logger("health_service", __name__)


class HealthService:
    def __init__(self, db: Database, storage_repo: StorageRepository):
        self.db = db
        self.storage_repo = storage_repo

    async def check_health(self) -> HealthCheckResponse:
        database_status = DatabaseStatus.UNKNOWN
        storage_status = DatabaseStatus.UNKNOWN
        overall_status = HealthStatus.OK
        detail_messages = []

        # Check database connection
        try:
            if self.db.client:
                # The 'ping' command is cheap and confirms connection is alive
                await self.db.client.admin.command("ping")
                database_status = DatabaseStatus.CONNECTED
            else:
                database_status = DatabaseStatus.DISCONNECTED
                overall_status = HealthStatus.ERROR
        except Exception as e:
            logger.error(f"Health check failed (DB Connection): {e}")
            database_status = DatabaseStatus.ERROR
            overall_status = HealthStatus.ERROR
            detail_messages.append(f"Database: {str(e)}")

        # Check Storage connection
        try:
            if await self.storage_repo.check_connection():
                storage_status = DatabaseStatus.CONNECTED
            else:
                storage_status = DatabaseStatus.DISCONNECTED
                overall_status = HealthStatus.ERROR
        except Exception as e:
            logger.error(f"Health check failed (Storage Connection): {e}")
            storage_status = DatabaseStatus.ERROR
            overall_status = HealthStatus.ERROR
            detail_messages.append(f"Storage: {str(e)}")

        detail = "; ".join(detail_messages) if detail_messages else None

        return HealthCheckResponse(
            status=overall_status,
            database=database_status,
            storage=storage_status,
            detail=detail,
        )
