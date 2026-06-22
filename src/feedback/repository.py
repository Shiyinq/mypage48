import uuid
from datetime import datetime
from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase


class FeedbackRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["feedback"]

    async def create(self, feedback_dict: dict) -> dict:
        feedback_dict["id"] = str(uuid.uuid4())
        feedback_dict["created_at"] = datetime.utcnow()
        await self.collection.insert_one(feedback_dict)
        return feedback_dict

    async def find_all(
        self, skip: int = 0, limit: int = 100, statuses: List[str] = None
    ) -> List[dict]:
        query = {}
        if statuses:
            query["status"] = {"$in": statuses}
        cursor = (
            self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def find_by_user_id(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        cursor = (
            self.collection.find({"user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def count(self, statuses: List[str] = None) -> int:
        query = {}
        if statuses:
            query["status"] = {"$in": statuses}
        return await self.collection.count_documents(query)

    async def count_by_user_id(self, user_id: str) -> int:
        return await self.collection.count_documents({"user_id": user_id})

    async def find_by_id(self, feedback_id: str) -> dict | None:
        return await self.collection.find_one({"id": feedback_id})

    async def update(self, feedback_id: str, update_data: dict) -> bool:
        result = await self.collection.update_one(
            {"id": feedback_id}, {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_by_id_and_user_id(self, feedback_id: str, user_id: str) -> bool:
        result = await self.collection.delete_one(
            {"id": feedback_id, "user_id": user_id}
        )
        return result.deleted_count > 0
