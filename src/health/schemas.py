from typing import Optional

from pydantic import BaseModel

from src.health.constants import DatabaseStatus, HealthStatus


class HealthCheckResponse(BaseModel):
    status: HealthStatus
    database: DatabaseStatus
    detail: Optional[str] = None
