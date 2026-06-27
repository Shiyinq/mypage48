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

    async def update_event_raw_data_detail(self, event_id: str, detail_data: dict):
        return await self.collection.update_one(
            {"id": event_id}, {"$set": {"raw_data.detail": detail_data}}
        )

    async def find_event_by_id(self, event_id: str) -> dict:
        pipeline = [
            {"$match": {"id": event_id}},
            {
                "$lookup": {
                    "from": "setlists",
                    "localField": "setlistId",
                    "foreignField": "setlistId",
                    "as": "setlist_docs",
                }
            },
            {
                "$lookup": {
                    "from": "members",
                    "localField": "memberIds",
                    "foreignField": "id",
                    "as": "members_docs",
                }
            },
            {
                "$lookup": {
                    "from": "members",
                    "localField": "seitansaiIds",
                    "foreignField": "id",
                    "as": "seitansai_members",
                }
            },
            {
                "$lookup": {
                    "from": "members",
                    "localField": "graduationIds",
                    "foreignField": "id",
                    "as": "graduation_members",
                }
            },
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
                    "members": "$members_docs",
                    "seitansaiMembers": {
                        "$map": {
                            "input": "$seitansai_members",
                            "as": "member",
                            "in": "$$member.name",
                        }
                    },
                    "graduationMembers": {
                        "$map": {
                            "input": "$graduation_members",
                            "as": "member",
                            "in": "$$member.name",
                        }
                    },
                }
            },
            {"$addFields": {"imageUrl": "$setlist_temp.imageUrl"}},
            {
                "$project": {
                    "setlist_docs": 0,
                    "setlist_temp": 0,
                    "members_docs": 0,
                    "graduation_members": 0,
                    "graduationIds": 0,
                    "seitansai_members": 0,
                    "seitansaiIds": 0,
                }
            },
        ]

        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if result:
            return result[0]
        return None

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
            # 3. Lookup Members for Graduation
            {
                "$lookup": {
                    "from": "members",
                    "localField": "graduationIds",
                    "foreignField": "id",
                    "as": "graduation_members",
                }
            },
            # 4. Add Fields: imageUrl, totalMembers, seitansaiMembers, and graduationMembers
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
                    "graduationMembers": {
                        "$map": {
                            "input": "$graduation_members",
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
                    "graduation_members": 0,
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
            # 3. Lookup Members for Graduation
            {
                "$lookup": {
                    "from": "members",
                    "localField": "graduationIds",
                    "foreignField": "id",
                    "as": "graduation_members",
                }
            },
            # 4. Add Fields: imageUrl, seitansaiMembers, and graduationMembers
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
                    "graduationMembers": {
                        "$map": {
                            "input": "$graduation_members",
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
                    "id": 1,
                    "title": 1,
                    "date": 1,
                    "url": 1,
                    "label": 1,
                    "type": 1,
                    "setlistId": 1,
                    "seitansaiMembers": 1,
                    "graduationMembers": 1,
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

    async def get_member_event_stats(self, member_id: str) -> dict:
        pipeline = [
            {"$match": {"memberIds": member_id}},
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "top_setlist": [
                        {
                            "$match": {
                                "setlistId": {"$exists": True, "$nin": [None, ""]}
                            }
                        },
                        {"$group": {"_id": "$setlistId", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 1},
                    ],
                    "unique_setlists": [
                        {
                            "$match": {
                                "setlistId": {"$exists": True, "$nin": [None, ""]}
                            }
                        },
                        {"$group": {"_id": "$setlistId"}},
                        {"$count": "count"},
                    ],
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return {
                "total_shows": 0,
                "top_setlist_id": None,
                "top_setlist_title": None,
                "top_setlist_count": 0,
                "unique_setlists": 0,
            }
        facet = result[0]
        total = facet.get("total", [])
        top = facet.get("top_setlist", [])
        unique = facet.get("unique_setlists", [])
        top_setlist_id = top[0]["_id"] if top else None
        top_setlist_title = None
        if top_setlist_id:
            setlist = await self.collection.database["setlists"].find_one(
                {"setlistId": top_setlist_id}, {"title": 1}
            )
            top_setlist_title = setlist["title"] if setlist else None
        return {
            "total_shows": total[0]["count"] if total else 0,
            "top_setlist_id": top_setlist_id,
            "top_setlist_title": top_setlist_title,
            "top_setlist_count": top[0]["count"] if top else 0,
            "unique_setlists": unique[0]["count"] if unique else 0,
        }

    async def count_member_events(self, member_id: str) -> int:
        """Count events for a specific member."""
        return await self.collection.count_documents({"memberIds": member_id})

    async def find_events_by_member_id_detailed(
        self, member_id: str, skip: int = 0, limit: int = 500
    ) -> List[dict]:
        """Find all events for a member with full detail (images, lookups)."""
        query = {"memberIds": member_id}

        pipeline = [
            {"$match": query},
            {"$sort": {"date": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "setlists",
                    "localField": "setlistId",
                    "foreignField": "setlistId",
                    "as": "setlist_docs",
                }
            },
            {
                "$lookup": {
                    "from": "members",
                    "localField": "seitansaiIds",
                    "foreignField": "id",
                    "as": "seitansai_members",
                }
            },
            {
                "$lookup": {
                    "from": "members",
                    "localField": "graduationIds",
                    "foreignField": "id",
                    "as": "graduation_members",
                }
            },
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
                    "graduationMembers": {
                        "$map": {
                            "input": "$graduation_members",
                            "as": "member",
                            "in": "$$member.name",
                        }
                    },
                }
            },
            {"$addFields": {"imageUrl": "$setlist_temp.imageUrl"}},
            {
                "$project": {
                    "setlist_docs": 0,
                    "setlist_temp": 0,
                    "graduation_members": 0,
                    "memberIds": 0,
                    "graduationIds": 0,
                    "seitansaiIds": 0,
                }
            },
        ]

        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=limit)
