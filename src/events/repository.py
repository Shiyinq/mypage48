from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.events.schemas import Event

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
                    "as": "setlist_docs"
                }
            },
            
            # 2. Add Fields: imageUrl and totalMembers
            {
                "$addFields": {
                    "setlist_temp": {"$arrayElemAt": ["$setlist_docs", 0]},
                    "totalMembers": {
                        "$cond": {
                            "if": {"$isArray": "$memberIds"},
                            "then": {"$size": "$memberIds"},
                            "else": 0
                        }
                    }
                }
            },
            
            # 3. Extract imageUrl from setlist_temp
            {
                "$addFields": {
                    "imageUrl": "$setlist_temp.imageUrl"
                }
            },
            
            # 4. Project: Exclude unwanted fields
            {
                "$project": {
                    "setlist_docs": 0,
                    "setlist_temp": 0,
                    "memberIds": 0,
                    "graduationIds": 0,
                    "seitansaiIds": 0,
                    # "setlist": 0, # We never added 'setlist' field in this new pipeline
                    # "members": 0, 
                    # "graduations": 0,
                    # "seitansais": 0
                }
            }
        ]
        
        cursor = self.collection.aggregate(pipeline)
        events = await cursor.to_list(length=limit)
        return events
