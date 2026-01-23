from datetime import datetime 
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from src.export.constants import ExportStatus
from src.export.schemas import ExportJob



class ExportRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["exports"]

    async def get_job(self, user_id: str) -> Optional[ExportJob]:
        doc = await self.collection.find_one({"user_id": user_id})
        if doc:
            return ExportJob(**doc)
        return None

    async def create_job(self, user_id: str) -> ExportJob:
        now = datetime.utcnow()
        job = ExportJob(
            user_id=user_id,
            status=ExportStatus.PROCESSING,
            created_at=now,
            updated_at=now
        )
        
        # Upsert: if exists, replace. Previous job is invalid if new one requested.
        # Actually user logic says check if processing. Service layer handles that.
        # Here we just save/overwrite.
        await self.collection.replace_one(
            {"user_id": user_id},
            job.model_dump(),
            upsert=True
        )
        return job

    async def update_status(
        self, 
        user_id: str, 
        status: ExportStatus, 
        file_path: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[ExportJob]:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if file_path:
            update_data["file_path"] = file_path
        if error:
            update_data["error"] = error
            
        doc = await self.collection.find_one_and_update(
            {"user_id": user_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if doc:
            return ExportJob(**doc)
        return None
        
    async def delete_job(self, user_id: str) -> bool:
        result = await self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0
