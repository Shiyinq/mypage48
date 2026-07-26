from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.concerts.schemas import CreateConcert, UpdateConcert


class ConcertsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["concerts"]

    async def insert_concert(self, concert_data: CreateConcert):
        return await self.collection.insert_one(concert_data.model_dump())

    async def find_concert_by_id(self, concert_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(concert_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(concert_id)})

    async def get_all_concerts(self) -> List[dict]:
        cursor = self.collection.find().sort("date", 1)  # Sort by date ascending
        return await cursor.to_list(length=None)

    async def update_concert(self, concert_id: str, update_data: UpdateConcert) -> bool:
        if not ObjectId.is_valid(concert_id):
            return False

        # Exclude unset fields
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return True  # Nothing to update

        result = await self.collection.update_one(
            {"_id": ObjectId(concert_id)}, {"$set": update_dict}
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def delete_concert(self, concert_id: str) -> bool:
        if not ObjectId.is_valid(concert_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(concert_id)})
        return result.deleted_count > 0
