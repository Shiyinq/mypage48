from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class NewsResponse(BaseModel):
    news_id: int
    title: str
    category: str
    link: str
    background_image: Optional[str] = None
    is_published: bool
    date: datetime
    valid_date_from: datetime
    content_body: str
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
