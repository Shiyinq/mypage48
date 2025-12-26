from pymongo.errors import ConnectionFailure

from src.database import Database
from src.health.constants import DatabaseStatus, HealthStatus
from src.health.schemas import HealthCheckResponse
from src.logging_config import create_logger

logger = create_logger("health_service", __name__)


class HealthService:
    def __init__(self, db: Database):
        self.db = db

    async def check_health(self) -> HealthCheckResponse:
        database_status = DatabaseStatus.UNKNOWN
        overall_status = HealthStatus.OK
        detail = None

        try:
            # Check database connection
            if self.db.client:
                # The 'ping' command is cheap and confirms connection is alive
                await self.db.client.admin.command("ping")
                database_status = DatabaseStatus.CONNECTED
            else:
                database_status = DatabaseStatus.DISCONNECTED
                overall_status = HealthStatus.ERROR

        except ConnectionFailure as e:
            logger.error(f"Health check failed (DB Connection): {e}")
            database_status = DatabaseStatus.ERROR
            overall_status = HealthStatus.ERROR
            detail = "Database connection failure"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            database_status = DatabaseStatus.ERROR
            overall_status = HealthStatus.ERROR
            detail = str(e)

        return HealthCheckResponse(
            status=overall_status,
            database=database_status,
            detail=detail,
        )
