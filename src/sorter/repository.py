from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.sorter.schemas import SorterInDB


class SortersRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["sorter_results"]

    async def create_sorter(self, sorter: SorterInDB):
        return await self.collection.insert_one(sorter.model_dump())

    async def get_sorter(self, sorter_id: str, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(sorter_id)
        except Exception:
            return None
        return await self.collection.find_one({"_id": oid, "user_id": user_id})

    async def get_sorters(self, user_id: str) -> List[dict]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def delete_sorter(self, sorter_id: str, user_id: str) -> bool:
        try:
            oid = ObjectId(sorter_id)
        except Exception:
            return False
        result = await self.collection.delete_one({"_id": oid, "user_id": user_id})
        return result.deleted_count > 0
