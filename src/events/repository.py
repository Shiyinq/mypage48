from datetime import datetime
from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase


class EventsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["events"]

    async def insert_event(self, event_data: dict):
        # Helper for seeding or manual creation if needed
        return await self.collection.insert_one(event_data)

    async def count_events(self, query: dict = None) -> int:
        if query is None:
            query = {}
        return await self.collection.count_documents(query)

    async def find_events_paginated(
        self, skip: int, limit: int, query: dict = None, sort_direction: int = 1
    ) -> List[dict]:
        if query is None:
            query = {}

        pipeline = [
            {"$match": query},
            {"$sort": {"date": sort_direction}},
            {"$skip": skip},
            {"$limit": limit},
            # 1. Lookup Setlist to get imageUrl
            {
                "$lookup": {
                    "from": "setlists",
                    "localField": "setlistId",
                    "foreignField": "setlistId",
                    "as": "setlist_docs",
                }
            },
            # 2. Lookup Members for Seitansai (Birthday celebrants)
            {
                "$lookup": {
                    "from": "members",
                    "localField": "seitansaiIds",
                    "foreignField": "id",
                    "as": "seitansai_members",
                }
            },
            # 3. Add Fields: imageUrl, totalMembers, and seitansaiMembers
            {
                "$addFields": {
                    "setlist_temp": {"$arrayElemAt": ["$setlist_docs", 0]},
                    "totalMembers": {
                        "$cond": {
                            "if": {"$isArray": "$memberIds"},
                            "then": {"$size": "$memberIds"},
                            "else": 0,
                        }
                    },
                    "seitansaiMembers": {
                        "$map": {
                            "input": "$seitansai_members",
                            "as": "member",
                            "in": "$$member.name",
                        }
                    },
                }
            },
            # 4. Extract imageUrl from setlist_temp
            {"$addFields": {"imageUrl": "$setlist_temp.imageUrl"}},
            # 5. Project: Exclude unwanted fields
            {
                "$project": {
                    "setlist_docs": 0,
                    "setlist_temp": 0,
                    "seitansai_members": 0,
                    "memberIds": 0,
                    "graduationIds": 0,
                    "seitansaiIds": 0,
                }
            },
        ]

        cursor = self.collection.aggregate(pipeline)
        events = await cursor.to_list(length=limit)
        return events

    async def find_events_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[dict]:
        query = {"date": {"$gte": start_date, "$lte": end_date}}

        # Reuse similar pipeline logic but for calendar (lighter version if possible, but user wants events so we need details)
        # We need same fields as paginated list for consistency in UI probably
        pipeline = [
            {"$match": query},
            {"$sort": {"date": 1}},
            # 1. Lookup Setlist to get imageUrl
            {
                "$lookup": {
                    "from": "setlists",
                    "localField": "setlistId",
                    "foreignField": "setlistId",
                    "as": "setlist_docs",
                }
            },
            # 2. Lookup Members for Seitansai (Birthday celebrants)
            {
                "$lookup": {
                    "from": "members",
                    "localField": "seitansaiIds",
                    "foreignField": "id",
                    "as": "seitansai_members",
                }
            },
            # 3. Add Fields: imageUrl, and seitansaiMembers
            {
                "$addFields": {
                    "setlist_temp": {"$arrayElemAt": ["$setlist_docs", 0]},
                    "seitansaiMembers": {
                        "$map": {
                            "input": "$seitansai_members",
                            "as": "member",
                            "in": "$$member.name",
                        }
                    },
                }
            },
            # 4. Project: Include ONLY necessary fields for Calendar
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "date": 1,
                    "url": 1,
                    "setlistId": 1,
                    "seitansaiMembers": 1,
                }
            },
        ]

        cursor = self.collection.aggregate(pipeline)
        # Return all events in range, usually not massive for one month
        events = await cursor.to_list(length=None)
        return events

    async def find_events_by_member_id(self, member_id: str) -> List[dict]:
        """Find all events where a specific member is present."""
        query = {"memberIds": member_id}

        projection = {"title": 1, "date": 1, "url": 1, "_id": 0}

        cursor = self.collection.find(query, projection)
        return await cursor.to_list(length=None)
