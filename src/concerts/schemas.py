from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ConcertBase(BaseModel):
    title: str
    theme: Optional[str] = "-"
    type: str = "Anniversary"
    date: datetime
    location: str
    details: str
    benefits: List[str] = Field(default_factory=list)
    ticket_price: List[str] = Field(default_factory=list)
    image: str = "https://placehold.co/600x800/2a2a2a/ffffff?text=Concert+Poster"


class CreateConcert(ConcertBase):
    pass


class UpdateConcert(BaseModel):
    title: Optional[str] = None
    theme: Optional[str] = None
    type: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    details: Optional[str] = None
    benefits: Optional[List[str]] = None
    ticket_price: Optional[List[str]] = None
    image: Optional[str] = None


class ConcertResponse(ConcertBase):
    id: str
