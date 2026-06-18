from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.feedback.constants import FeedbackType


class FeedbackBase(BaseModel):
    type: FeedbackType
    message: str = Field(..., min_length=10, max_length=1000)
    name: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    email: Optional[EmailStr] = None


class FeedbackResponse(FeedbackBase):
    id: str
    created_at: datetime


class FeedbackPaginationResponse(BaseModel):
    data: list[FeedbackResponse]
    page: int
    limit: int
    total: int
    has_more: bool
