from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.logging_config import create_logger


class ReplayRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.col = db.replay
        self.logger = create_logger("replay_repository", __name__)

    async def insert(self, data: dict[str, Any]) -> str:
        result = await self.col.insert_one(data)
        return str(result.inserted_id)

    async def find_by_live_id(self, live_id: str) -> Optional[dict[str, Any]]:
        return await self.col.find_one({"live_id": live_id})

    async def find_all(self) -> list[dict[str, Any]]:
        cursor = self.col.find({}).sort("recording_ended_at", -1)
        return await cursor.to_list(length=None)

    async def exists(self, live_id: str) -> bool:
        doc = await self.col.find_one({"live_id": live_id}, {"_id": 1})
        return doc is not None

    async def update_youtube_id(self, live_id: str, youtube_id: str) -> bool:
        result = await self.col.update_one(
            {"live_id": live_id},
            {
                "$set": {
                    "youtube_id": youtube_id,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.modified_count > 0
