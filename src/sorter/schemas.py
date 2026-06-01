from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, BeforeValidator, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class SorterResultItem(BaseModel):
    id: str
    name: str
    rank: int


class SorterCreateRequest(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    filters: List[str] = Field(default_factory=list)
    results: List[SorterResultItem]


class SorterInDB(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    filters: List[str]
    results: List[SorterResultItem]
    created_at: datetime
    updated_at: datetime


class SorterResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: str
    title: str
    description: Optional[str] = None
    filters: List[str]
    results: List[SorterResultItem]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
