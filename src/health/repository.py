import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class HealthRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["recorder_heartbeats"]

    async def upsert_recorder_heartbeat(
        self,
        mode: str,
        encrypted_bot_token: Optional[str],
        encrypted_chat_id: Optional[str],
    ):
        """
        Upsert recorder heartbeat data per mode, implementing transition cleanup logic.
        """
        now = datetime.datetime.now(datetime.timezone.utc)

        # Transition cleanup
        if mode == "all":
            # Delete all documents that are NOT "all"
            await self.collection.delete_many({"_id": {"$ne": "recorder_all"}})
        else:
            # Delete the "all" document if it exists, since we are moving to specific modes
            await self.collection.delete_one({"_id": "recorder_all"})

        doc_id = f"recorder_{mode}"
        update_doc = {
            "$set": {
                "mode": mode,
                "encrypted_bot_token": encrypted_bot_token,
                "encrypted_chat_id": encrypted_chat_id,
                "updated_at": now,
            },
            "$setOnInsert": {"is_down": False},
        }

        await self.collection.update_one({"_id": doc_id}, update_doc, upsert=True)

    async def get_all_heartbeats(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find({})
        return await cursor.to_list(length=100)

    async def mark_as_down(self, doc_id: str):
        await self.collection.update_one({"_id": doc_id}, {"$set": {"is_down": True}})

    async def mark_as_up(self, doc_id: str):
        await self.collection.update_one({"_id": doc_id}, {"$set": {"is_down": False}})
