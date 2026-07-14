from typing import Optional

from pydantic import BaseModel

from src.health.constants import DatabaseStatus, HealthStatus


class HealthCheckResponse(BaseModel):
    status: HealthStatus
    database: DatabaseStatus
    storage: DatabaseStatus
    detail: Optional[str] = None


class RecorderHeartbeatRequest(BaseModel):
    mode: str
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
