from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase


class AdminRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def count_documents(
        self, collection_name: str, query: Dict[str, Any] = None
    ) -> int:
        if query is None:
            query = {}
        return await self.db[collection_name].count_documents(query)

    async def aggregate(
        self, collection_name: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        cursor = self.db[collection_name].aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def find(
        self, collection_name: str, query: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        if query is None:
            query = {}
        return await self.db[collection_name].find(query).to_list(length=None)
