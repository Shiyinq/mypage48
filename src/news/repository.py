import math
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class NewsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["news"]

    async def get_news(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get paginated news."""
        skip = (page - 1) * limit
        # Sort by valid_date_from descending
        cursor = (
            self.collection.find({}).sort("valid_date_from", -1).skip(skip).limit(limit)
        )
        items = await cursor.to_list(length=limit)

        total = await self.collection.count_documents({})
        total_page = math.ceil(total / limit) if limit > 0 else 0

        return {
            "data": items,
            "meta": {
                "page": page,
                "limit_per_page": limit,
                "total_page": total_page,
                "count_per_page": len(items),
                "count_total": total,
            },
        }

    async def get_news_by_link(self, link: str) -> Optional[Dict[str, Any]]:
        """Get a single news item by link."""
        return await self.collection.find_one({"link": link})
