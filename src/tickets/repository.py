from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from src.tickets.schemas import TicketInDB, TicketUpdateRequest


class TicketsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["tickets"]

    async def create_ticket(self, ticket: TicketInDB):
        return await self.collection.insert_one(ticket.model_dump(exclude_none=True))

    async def get_ticket(self, ticket_id: str, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(ticket_id)
        except:
            return None
        return await self.collection.find_one({"_id": oid, "user_id": user_id})

    async def get_tickets(
        self,
        user_id: str,
        year: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        title: Optional[str] = None,
        has_two_shot: Optional[bool] = None,
        days: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_favorite: Optional[bool] = None,
    ) -> tuple[List[dict], int]:
        query = {"user_id": user_id}

        if year:
            # event.date is stored as string "YYYY-MM-DD", so use regex to match the year prefix
            query["event.date"] = {"$regex": f"^{year}-"}

        if title:
            query["event.title"] = {"$regex": title, "$options": "i"}

        if has_two_shot:
            query["two_shot"] = {"$ne": None}

        if is_favorite is not None:
            query["is_favorite"] = is_favorite if is_favorite else {"$ne": True}

        if days:
            # days is a list of strings like ["Saturday", "Sunday"]
            # event.day stores the day name
            upper_days = [d.upper() for d in days]
            query["$expr"] = {"$in": [{"$toUpper": "$event.day"}, upper_days]}

        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date

            # Merge with existing event.date query if year was set (though usually mutually exclusive)
            if "event.date" in query:
                # If both year and range existing, we might need $and, but usually year is for one view
                # and range for another. For safety let's use $and if needed or assume query construction
                pass

            query["event.date"] = date_query

        # Refinement: If year is set, it might conflict with start_date/end_date if not careful.
        # But based on usage, year is usually top-level filter.
        # If start_date/end_date is provided, we should probably ignore 'year' or ensure they are compatible.
        # For now, let's let start_date/end_date override or combine.
        # Actually simplest is: if start/end date provided, they take optimized precedence for the date field.
        if start_date or end_date:
            query["event.date"] = {}
            if start_date:
                query["event.date"]["$gte"] = start_date
            if end_date:
                query["event.date"]["$lte"] = end_date
            # If year was set, verify compatibility? Or just let range rule.
            # Ideally range filter implies we don't care about the generic 'year' param unless it limits further.
            # Let's assume range filter supersedes generic year check for the date field.

        total_count = await self.collection.count_documents(query)

        cursor = self.collection.find(query).sort(
            [("event.date", -1), ("event.time", -1)]
        )

        if page is not None and limit is not None:
            skip = (page - 1) * limit
            cursor = cursor.skip(skip).limit(limit)

        return await cursor.to_list(length=None), total_count

    async def update_ticket(
        self, ticket_id: str, user_id: str, update_data: TicketUpdateRequest
    ) -> Optional[dict]:
        try:
            oid = ObjectId(ticket_id)
        except:
            return None

        # Use exclude_unset=True to only include fields that were explicitly set in the request.
        # This allows distinguishing between "field not provided" (don't update) and "field set to null" (delete/unset).
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            return await self.get_ticket(ticket_id, user_id)

        # Update updated_at
        update_dict["updated_at"] = datetime.now(timezone.utc)

        # Use $set to update specific fields
        # Note: Simply setting keys might overwrite nested objects if not careful,
        # but current schema allows full replacement of 'event' or 'seat' which is usually fine for this usecase.
        # Ideally we might want dot notation for partial nested updates, but we'll assume full component updates (e.g. sending full Event obj)

        return await self.collection.find_one_and_update(
            {"_id": oid, "user_id": user_id},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER,
        )

    async def delete_ticket(self, ticket_id: str, user_id: str) -> bool:
        try:
            oid = ObjectId(ticket_id)
        except:
            return False
        result = await self.collection.delete_one({"_id": oid, "user_id": user_id})
        return result.deleted_count > 0

    async def get_available_years(self, user_id: str) -> List[int]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            # Handle potentially missing or invalid dates safely
            {
                "$match": {
                    "event.date": {
                        "$exists": True,
                        "$type": "string",
                        "$regex": r"^\d{4}-\d{2}-\d{2}",
                    }
                }
            },
            {
                "$project": {
                    "year": {
                        "$year": {
                            "$dateFromString": {
                                "dateString": "$event.date",
                                "format": "%Y-%m-%d",
                            }
                        }
                    }
                }
            },
            {"$group": {"_id": "$year"}},
            {"$sort": {"_id": -1}},
        ]
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        return [r["_id"] for r in results if r["_id"] is not None]

    async def get_tickets_filtered(
        self,
        user_id: str,
        year: Optional[int],
        start_month: int,
        end_month: int,
        is_all_data: bool,
    ) -> List[dict]:
        pipeline = [{"$match": {"user_id": user_id}}]

        if not is_all_data and year is not None:
            pipeline.extend(
                [
                    # Ensure date field validity for parsing
                    {
                        "$match": {
                            "event.date": {
                                "$exists": True,
                                "$type": "string",
                                "$regex": r"^\d{4}-\d{2}-\d{2}",
                            }
                        }
                    },
                    {
                        "$addFields": {
                            "parsedDate": {
                                "$dateFromString": {
                                    "dateString": "$event.date",
                                    "format": "%Y-%m-%d",
                                }
                            }
                        }
                    },
                    {
                        "$addFields": {
                            "year": {"$year": "$parsedDate"},
                            "month": {"$month": "$parsedDate"},  # 1-12
                        }
                    },
                    {
                        "$match": {
                            "year": year,
                            "month": {"$gte": start_month + 1, "$lte": end_month + 1},
                        }
                    },
                    # Cleanup temp fields (optional but cleaner result)
                    {"$project": {"parsedDate": 0, "year": 0, "month": 0}},
                ]
            )

        pipeline.append({"$sort": {"event.date": -1, "event.time": -1}})

        return await self.collection.aggregate(pipeline).to_list(length=None)

    async def get_distinct_titles(self, user_id: str) -> List[str]:
        return await self.collection.distinct("event.title", {"user_id": user_id})

    async def toggle_two_shot_favorite(
        self, ticket_id: str, user_id: str
    ) -> Optional[dict]:
        try:
            oid = ObjectId(ticket_id)
        except:
            return None

        ticket = await self.get_ticket(ticket_id, user_id)
        if not ticket:
            return None

        current = ticket.get("two_shot", {})
        if not current:
            return None

        new_value = not current.get("is_favorite", False)

        return await self.collection.find_one_and_update(
            {"_id": oid, "user_id": user_id},
            {
                "$set": {
                    "two_shot.is_favorite": new_value,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    async def toggle_favorite(self, ticket_id: str, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(ticket_id)
        except:
            return None

        ticket = await self.get_ticket(ticket_id, user_id)
        if not ticket:
            return None

        new_value = not ticket.get("is_favorite", False)

        return await self.collection.find_one_and_update(
            {"_id": oid, "user_id": user_id},
            {
                "$set": {
                    "is_favorite": new_value,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    async def delete_ticket_photo(
        self, ticket_id: str, user_id: str, photo_type: str
    ) -> Optional[dict]:
        try:
            oid = ObjectId(ticket_id)
        except:
            return None

        update_query = {}
        if photo_type == "ticket":
            update_query = {
                "imageUrl": None,
                "imageUrl_medium": None,
                "imageUrl_small": None,
                "blurHash": None,
            }
        elif photo_type == "twoshot":
            update_query = {
                "two_shot.imageUrl": None,
                "two_shot.imageUrl_medium": None,
                "two_shot.imageUrl_small": None,
                "two_shot.blurHash": None,
            }
        else:
            return None

        update_query["updated_at"] = datetime.now(timezone.utc)

        return await self.collection.find_one_and_update(
            {"_id": oid, "user_id": user_id},
            {"$set": update_query},
            return_document=ReturnDocument.AFTER,
        )
