from typing import List, Optional

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

    async def get_next_id(self) -> int:
        """Get the next available member ID"""
        result = await self.collection.find_one(
            {}, sort=[("id", -1)], projection={"id": 1}
        )
        return (result.get("id", 0) + 1) if result else 1

    async def insert_one(self, member: dict) -> dict:
        """Insert a single member and return it"""
        await self.collection.insert_one(member)
        return await self.find_by_id(member["id"])

    async def update_one(self, member_id: int, update_data: dict) -> Optional[dict]:
        """Update a member by ID and return the updated document"""
        result = await self.collection.update_one(
            {"id": member_id}, {"$set": update_data}
        )
        if result.modified_count == 0:
            return None
        return await self.find_by_id(member_id)

    async def delete_one(self, member_id: int) -> bool:
        """Delete a member by ID and return True if successful"""
        result = await self.collection.delete_one({"id": member_id})
        return result.deleted_count > 0
