from datetime import datetime, timezone
import re
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def insert_user(self, user_data: dict):
        return await self.collection.insert_one(user_data)

    async def find_one(self, query: dict) -> Optional[dict]:
        return await self.collection.find_one(query)

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        user = await self.collection.find_one({"userId": user_id})
        return user

    async def get_users_by_ids(self, user_ids: list[str]) -> list[dict]:
        """Fetch multiple users by their userId in a single query."""
        if not user_ids:
            return []
        cursor = self.collection.find({"userId": {"$in": user_ids}})
        return await cursor.to_list(length=None)

    async def get_users_by_usernames(self, usernames: list[str]) -> list[dict]:
        """Fetch multiple users by their (lower-cased) username in one query."""
        if not usernames:
            return []
        cursor = self.collection.find({"username": {"$in": usernames}})
        return await cursor.to_list(length=None)

    async def search_users(self, term: str, limit: int = 20) -> list[dict]:
        """Accounts matching a username prefix or a display-name substring.

        Usernames are stored lower-cased, so an anchored pattern stays on the
        unique index; the display name has no index and is a small scan.
        """
        if not term:
            return []
        escaped = re.escape(term)
        query = {
            "$or": [
                {"username": {"$regex": f"^{escaped}"}},
                {"name": {"$regex": escaped, "$options": "i"}},
            ]
        }
        cursor = self.collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)

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

    async def add_oshi_id(self, user_id: str, oshi_id: str):
        return await self.collection.update_one(
            {"userId": user_id}, {"$addToSet": {"oshiIds": oshi_id}}
        )

    async def remove_oshi_id(self, user_id: str, oshi_id: str):
        return await self.collection.update_one(
            {"userId": user_id}, {"$pull": {"oshiIds": oshi_id}}
        )

    async def set_public_status(
        self, user_id: str, is_public: bool, public_year: Optional[int] = None
    ):
        update_data = {"isPublic": is_public}
        if is_public:
            update_data["publicYear"] = public_year
        else:
            update_data["publicYear"] = None

        return await self.collection.update_one(
            {"userId": user_id}, {"$set": update_data}
        )

    async def set_profile_picture(
        self, user_id: str, profile_picture: str, blur_hash: Optional[str] = None
    ):
        update_data = {"profilePicture": profile_picture}
        if blur_hash:
            update_data["blurHash"] = blur_hash

        return await self.collection.update_one(
            {"userId": user_id}, {"$set": update_data}
        )

    async def set_banner_picture(
        self, user_id: str, banner_picture: str, blur_hash: Optional[str] = None
    ):
        update_data = {"bannerPicture": banner_picture}
        if blur_hash:
            update_data["bannerBlurHash"] = blur_hash

        return await self.collection.update_one(
            {"userId": user_id}, {"$set": update_data}
        )

    async def update_last_active(self, user_id: str):
        return await self.collection.update_one(
            {"userId": user_id}, {"$set": {"lastActiveAt": datetime.now(timezone.utc)}}
        )

    async def get_all_paginated(
        self, page: int, limit: int, search: str | None = None
    ) -> list[dict]:
        """Get paginated list of users with optional search."""
        query = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"username": {"$regex": search, "$options": "i"}},
            ]

        skip = (page - 1) * limit
        cursor = (
            self.collection.find(query).skip(skip).limit(limit).sort("createdAt", -1)
        )
        return await cursor.to_list(length=limit)

    async def count_all(self, search: str | None = None) -> int:
        """Count total users with optional search filter."""
        query = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"username": {"$regex": search, "$options": "i"}},
            ]
        return await self.collection.count_documents(query)
