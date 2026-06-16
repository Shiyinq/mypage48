from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class NewsResponse(BaseModel):
    news_id: int
    title: str
    category: str
    link: str
    background_image: Optional[str] = None
    blurHash: Optional[str] = None
    is_published: bool
    valid_date_from: datetime
    content_body: str

    @field_validator("valid_date_from", mode="after")
    @classmethod
    def force_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    short_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    page: int
    limit_per_page: int
    total_page: int
    count_per_page: int
    count_total: int


class NewsPaginationResponse(BaseModel):
    data: List[NewsResponse]
    meta: PaginationMeta
