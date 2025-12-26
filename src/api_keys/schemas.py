from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CreateAPIKey(BaseModel):
    userId: str
    hashKey: str
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), example=None
    )
    lastUsedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), example=None
    )


class APIKeysResponse(BaseModel):
    detail: str
    apiKey: str
