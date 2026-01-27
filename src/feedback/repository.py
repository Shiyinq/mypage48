import uuid
from datetime import datetime
from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.feedback.schemas import FeedbackCreate


class FeedbackRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["feedback"]

    async def create(self, feedback: FeedbackCreate) -> dict:
        feedback_dict = feedback.model_dump()
        feedback_dict["id"] = str(uuid.uuid4())
        feedback_dict["created_at"] = datetime.utcnow()
        await self.collection.insert_one(feedback_dict)
        return feedback_dict

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count(self) -> int:
        return await self.collection.count_documents({})
