from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.tickets.schemas import TicketInDB, TicketUpdateRequest
from pymongo import ReturnDocument
from bson import ObjectId


class TicketsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["tickets"]

    async def create_ticket(self, ticket: TicketInDB):
        return await self.collection.insert_one(ticket.model_dump())

    async def get_ticket(self, ticket_id: str, user_id: str) -> Optional[dict]:
        try:
            oid = ObjectId(ticket_id)
        except:
            return None
        return await self.collection.find_one({"_id": oid, "user_id": user_id})
    
    async def get_all_tickets(
        self, 
        user_id: str, 
        year: Optional[int] = None, 
        page: Optional[int] = None, 
        limit: Optional[int] = None
    ) -> tuple[List[dict], int]:
        query = {"user_id": user_id}
        
        if year:
            # event.date is stored as string "YYYY-MM-DD", so use regex to match the year prefix
            query["event.date"] = {"$regex": f"^{year}-"}
            
        total_count = await self.collection.count_documents(query)
        
        cursor = self.collection.find(query).sort([("event.date", -1), ("event.time", -1)])
        
        if page is not None and limit is not None:
            skip = (page - 1) * limit
            cursor = cursor.skip(skip).limit(limit)
            
        return await cursor.to_list(length=None), total_count

    async def update_ticket(self, ticket_id: str, user_id: str, update_data: TicketUpdateRequest) -> Optional[dict]:
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
        from datetime import datetime, timezone
        update_dict["updated_at"] = datetime.now(timezone.utc)

        # Use $set to update specific fields
        # Note: Simply setting keys might overwrite nested objects if not careful, 
        # but current schema allows full replacement of 'event' or 'seat' which is usually fine for this usecase.
        # Ideally we might want dot notation for partial nested updates, but we'll assume full component updates (e.g. sending full Event obj)
        
        return await self.collection.find_one_and_update(
            {"_id": oid, "user_id": user_id},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER
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
            {"$match": {"event.date": {"$exists": True, "$type": "string", "$regex": r"^\d{4}-\d{2}-\d{2}"}}},
            {"$project": {
                "year": {
                    "$year": {"$dateFromString": {"dateString": "$event.date", "format": "%Y-%m-%d"}}
                }
            }},
            {"$group": {"_id": "$year"}},
            {"$sort": {"_id": -1}}
        ]
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        return [r["_id"] for r in results if r["_id"] is not None]

    async def get_tickets_filtered(
        self, 
        user_id: str, 
        year: Optional[int], 
        start_month: int, 
        end_month: int, 
        is_all_data: bool
    ) -> List[dict]:
        pipeline = [{"$match": {"user_id": user_id}}]

        if not is_all_data and year is not None:
             pipeline.extend([
                # Ensure date field validity for parsing
                {"$match": {"event.date": {"$exists": True, "$type": "string", "$regex": r"^\d{4}-\d{2}-\d{2}"}}},
                {"$addFields": {
                    "parsedDate": {
                        "$dateFromString": {
                            "dateString": "$event.date",
                            "format": "%Y-%m-%d"
                        }
                    }
                }},
                {"$addFields": {
                    "year": {"$year": "$parsedDate"},
                    "month": {"$month": "$parsedDate"}  # 1-12
                }},
                {"$match": {
                    "year": year,
                    "month": {"$gte": start_month + 1, "$lte": end_month + 1}
                }},
                # Cleanup temp fields (optional but cleaner result)
                {"$project": {"parsedDate": 0, "year": 0, "month": 0}}
            ])
        
        pipeline.append({"$sort": {"event.date": -1, "event.time": -1}})
        
        return await self.collection.aggregate(pipeline).to_list(length=None)
