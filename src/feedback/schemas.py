from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.feedback.constants import FeedbackStatus, FeedbackType


class FeedbackBase(BaseModel):
    type: FeedbackType
    message: str = Field(..., min_length=10, max_length=1000)
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackResponse(FeedbackBase):
    id: str
    status: FeedbackStatus = FeedbackStatus.PENDING
    user_id: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime


class FeedbackUpdateStatus(BaseModel):
    status: FeedbackStatus
    admin_notes: Optional[str] = Field(None, max_length=1000)


class PaginationMeta(BaseModel):
    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class FeedbackPaginationResponse(BaseModel):
    data: list[FeedbackResponse]
    meta: PaginationMeta
