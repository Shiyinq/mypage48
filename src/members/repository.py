from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase


class MemberRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["members"]

    async def insert_many(self, members: List[dict]) -> int:
        result = await self.collection.insert_many(members)
        return len(result.inserted_ids)

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        generation: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[dict]:
        query = {}

        if generation:
            query["generation"] = generation

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"nickname": {"$regex": search, "$options": "i"}},
            ]

        cursor = self.collection.find(query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count(
        self, generation: Optional[str] = None, search: Optional[str] = None
    ) -> int:
        query = {}

        if generation:
            query["generation"] = generation

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"nickname": {"$regex": search, "$options": "i"}},
            ]

        return await self.collection.count_documents(query)

    async def find_by_id(self, member_id: int) -> Optional[dict]:
        return await self.collection.find_one({"id": member_id})

    async def find_by_nickname(self, nickname: str) -> Optional[dict]:
        return await self.collection.find_one(
            {"nickname": {"$regex": f"^{nickname}$", "$options": "i"}}
        )

    async def delete_all(self) -> int:
        result = await self.collection.delete_many({})
        return result.deleted_count

    async def get_generations(self) -> List[str]:
        """Get list of unique generations"""
        generations = await self.collection.distinct("generation")
        return sorted([g for g in generations if g])
