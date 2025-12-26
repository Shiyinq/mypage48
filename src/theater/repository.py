from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.theater.schemas import TicketInDB, TicketUpdateRequest
from pymongo import ReturnDocument
from bson import ObjectId


class TheaterRepository:
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
    
    async def get_all_tickets(self, user_id: str) -> List[dict]:
        cursor = self.collection.find({"user_id": user_id}).sort("event.date", -1)
        return await cursor.to_list(length=None)

    async def update_ticket(self, ticket_id: str, user_id: str, update_data: TicketUpdateRequest) -> Optional[dict]:
        try:
            oid = ObjectId(ticket_id)
        except:
            return None
        
        # Filter out None values
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
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
