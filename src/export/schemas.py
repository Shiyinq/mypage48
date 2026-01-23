from datetime import datetime

from typing import Optional

from pydantic import BaseModel, ConfigDict 

from src.export.constants import ExportStatus

class ExportJob(BaseModel):
    user_id: str
    status: ExportStatus
    created_at: datetime
    updated_at: datetime
    file_path: Optional[str] = None  # MinIO path
    error: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ExportResponse(BaseModel):
    status: ExportStatus
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
