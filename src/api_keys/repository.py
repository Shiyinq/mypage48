from datetime import datetime, timezone
from typing import Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.api_keys.schemas import CreateAPIKey


class ApiKeyRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["api_keys"]

    async def insert_api_key(self, api_key_data: CreateAPIKey):
        return await self.collection.insert_one(api_key_data.model_dump())

    async def find_user_api_key(self, user_id: str) -> Optional[dict]:
        return await self.collection.find_one({"userId": user_id})

    async def delete_user_api_key(self, user_id: str):
        return await self.collection.delete_one({"userId": user_id})

    async def update_last_used_api_key(self, user_id: str):
        return await self.collection.update_one(
            {"userId": user_id}, {"$set": {"lastUsedAt": datetime.now(timezone.utc)}}
        )

    async def find_user_by_hash_key(self, hash_key: str) -> Optional[Dict]:
        pipeline = [
            {"$match": {"hashKey": hash_key}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "userId",
                    "foreignField": "userId",
                    "as": "user",
                }
            },
            {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "userId": 1,
                    "profilePicture": "$user.profilePicture",
                    "name": "$user.name",
                    "username": "$user.username",
                    "email": "$user.email",
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return result[0] if result else None
