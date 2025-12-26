from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class AuthRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.refresh_tokens = db["refresh_tokens"]
        self.login_history = db["login_history"]

    async def insert_refresh_token(self, data: dict):
        return await self.refresh_tokens.insert_one(data)

    async def find_refresh_token(self, token: str) -> Optional[dict]:
        return await self.refresh_tokens.find_one({"hashRefreshToken": token})

    async def update_refresh_token_last_used(self, token: str):
        return await self.refresh_tokens.update_one(
            {"hashRefreshToken": token},
            {"$set": {"lastUsedAt": datetime.now(timezone.utc)}},
        )

    async def delete_refresh_token(self, token: str):
        return await self.refresh_tokens.delete_one({"hashRefreshToken": token})

    async def insert_login_history(self, data: dict):
        return await self.login_history.insert_one(data)

    async def find_last_login_history(self, user_id: str) -> Optional[dict]:
        return await self.login_history.find_one(
            {"userId": user_id}, sort=[("loginAt", -1)]
        )

    # Verification Tokens
    async def delete_verification_tokens_by_user(self, user_id: str, token_type: str):
        return await self.db["verification_tokens"].delete_many(
            {"userId": user_id, "tokenType": token_type}
        )

    async def insert_verification_token(self, data: dict):
        return await self.db["verification_tokens"].insert_one(data)

    async def find_verification_token(
        self, token: str, token_type: str
    ) -> Optional[dict]:
        return await self.db["verification_tokens"].find_one(
            {"hashToken": token, "tokenType": token_type}
        )

    async def delete_verification_token(self, token: str, token_type: str):
        return await self.db["verification_tokens"].delete_one(
            {"hashToken": token, "tokenType": token_type}
        )
