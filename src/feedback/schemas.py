from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


from src.feedback.constants import FeedbackType


class FeedbackCreate(BaseModel):
    type: FeedbackType
    message: str = Field(..., min_length=10, max_length=1000)
    email: Optional[EmailStr] = None
    name: Optional[str] = None


class FeedbackResponse(FeedbackCreate):
    id: str
    created_at: datetime


class FeedbackPaginationResponse(BaseModel):
    data: list[FeedbackResponse]
    page: int
    limit: int
    total: int
    has_more: bool
