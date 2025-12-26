from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def insert_user(self, user_data: dict):
        return await self.collection.insert_one(user_data)

    async def find_one(self, query: dict) -> Optional[dict]:
        return await self.collection.find_one(query)

    async def update_one(self, filter_query: dict, update_data: dict):
        return await self.collection.update_one(filter_query, update_data)

    async def increment_failed_login_attempts(self, user_id: str):
        return await self.collection.update_one(
            {"userId": user_id}, {"$inc": {"failedLoginAttempts": 1}}
        )

    async def reset_failed_login_attempts(self, user_id: str):
        return await self.collection.update_one(
            {"userId": user_id}, {"$set": {"failedLoginAttempts": 0}}
        )

    async def lock_account(self, user_id: str, locked_until):
        return await self.collection.update_one(
            {"userId": user_id},
            {"$set": {"isAccountLocked": True, "accountLockedUntil": locked_until}},
        )

    async def unlock_account(self, user_id: str):
        return await self.collection.update_one(
            {"userId": user_id},
            {
                "$set": {
                    "isAccountLocked": False,
                    "accountLockedUntil": None,
                    "failedLoginAttempts": 0,
                }
            },
        )

    async def set_email_verified(self, user_id: str):
        return await self.collection.update_one(
            {"userId": user_id}, {"$set": {"isEmailVerified": True}}
        )
