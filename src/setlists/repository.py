from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class SetlistsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["setlists"]
        self.db = db

    async def insert_many(self, setlists: List[dict]) -> int:
        result = await self.collection.insert_many(setlists)
        return len(result.inserted_ids)

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        setlist_type: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> List[dict]:
        query = {}

        if setlist_type:
            query["type"] = setlist_type

        if active is not None:
            query["active"] = active

        cursor = self.collection.find(query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_all_with_stats(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        setlist_type: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> tuple[List[dict], int]:
        """
        Get all setlists with ticket count stats using aggregation.
        Returns (setlists_with_stats, max_attendance)
        """
        pipeline = []

        # Match stage for filtering
        match_query = {}
        if setlist_type:
            match_query["type"] = setlist_type
        if active is not None:
            match_query["active"] = active

        if match_query:
            pipeline.append({"$match": match_query})

        # Lookup tickets and count matches
        # Note: tickets collection uses "user_id" field (snake_case)
        if user_id:
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "tickets",
                            "let": {"setlist_title": {"$toLower": "$title"}},
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$and": [
                                                {"$eq": ["$user_id", user_id]},
                                                {
                                                    "$regexMatch": {
                                                        "input": {
                                                            "$toLower": "$event.title"
                                                        },
                                                        "regex": "$$setlist_title",
                                                    }
                                                },
                                            ]
                                        }
                                    }
                                }
                            ],
                            "as": "matched_tickets",
                        }
                    },
                    {"$addFields": {"count": {"$size": "$matched_tickets"}}},
                    {
                        "$project": {
                            "matched_tickets": 0  # Remove the matched tickets array
                        }
                    },
                ]
            )
        else:
            # No user, count is 0
            pipeline.append({"$addFields": {"count": 0}})

        # Sort by active (desc) then count (desc) then title (asc)
        pipeline.append({"$sort": {"active": -1, "count": -1, "title": 1}})

        # Skip and limit
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit)

        # Calculate max attendance
        max_attendance = max((r.get("count", 0) for r in results), default=0)

        return results, max_attendance

    async def count(
        self,
        setlist_type: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> int:
        query = {}

        if setlist_type:
            query["type"] = setlist_type

        if active is not None:
            query["active"] = active

        return await self.collection.count_documents(query)

    async def find_by_setlist_id(self, setlist_id: str) -> Optional[dict]:
        """Find by setlistId (UUID) field"""
        return await self.collection.find_one({"setlistId": setlist_id})

    async def find_by_title(self, title: str) -> Optional[dict]:
        return await self.collection.find_one(
            {"title": {"$regex": f"^{title}$", "$options": "i"}}
        )

    async def delete_all(self) -> int:
        result = await self.collection.delete_many({})
        return result.deleted_count

    async def get_types(self) -> List[str]:
        """Get list of unique setlist types"""
        types = await self.collection.distinct("type")
        return sorted([t for t in types if t])

    async def find_with_tickets(
        self,
        setlist_id: str,
        user_id: str,
    ) -> Optional[dict]:
        """
        Get setlist by ID with user's matching tickets.
        Returns setlist with 'matched_tickets' array containing ticket data.
        """
        pipeline = [
            {"$match": {"setlistId": setlist_id}},
            {
                "$lookup": {
                    "from": "tickets",
                    "let": {"setlist_title": {"$toLower": "$title"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$user_id", user_id]},
                                        {
                                            "$regexMatch": {
                                                "input": {"$toLower": "$event.title"},
                                                "regex": "$$setlist_title",
                                            }
                                        },
                                    ]
                                }
                            }
                        },
                        {"$sort": {"event.date": 1}},  # Sort by date ascending
                        {
                            "$project": {
                                "_id": 1,
                                "ticketId": {"$toString": "$_id"},
                                "event": 1,
                                "seat": 1,
                                "price": 1,
                                "notes": 1,
                            }
                        },
                    ],
                    "as": "matched_tickets",
                }
            },
            {"$addFields": {"count": {"$size": "$matched_tickets"}}},
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        return results[0] if results else None

    async def get_max_attendance(self, user_id: str) -> int:
        """Get the maximum ticket count for any setlist for this user"""
        pipeline = [
            {
                "$lookup": {
                    "from": "tickets",
                    "let": {"setlist_title": {"$toLower": "$title"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$user_id", user_id]},
                                        {
                                            "$regexMatch": {
                                                "input": {"$toLower": "$event.title"},
                                                "regex": "$$setlist_title",
                                            }
                                        },
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "matched_tickets",
                }
            },
            {"$addFields": {"count": {"$size": "$matched_tickets"}}},
            {"$group": {"_id": None, "maxCount": {"$max": "$count"}}},
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        return results[0].get("maxCount", 1) if results else 1
