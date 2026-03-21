from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class EventTeam(BaseModel):
    id: str
    img: str


class Event(BaseModel):
    id: str
    title: str
    date: datetime
    url: str
    label: str
    type: Optional[str] = None

    # List View Fields
    imageUrl: Optional[str] = None
    totalMembers: int = 0
    seitansaiMembers: Optional[List[str]] = None
    setlistId: Optional[str] = None
    team: Optional[EventTeam] = None

    class Config:
        populate_by_name = True


class CalendarEvent(BaseModel):
    title: str
    date: datetime
    url: str
    label: Optional[str] = None
    type: Optional[str] = None
    setlistId: Optional[str] = None
    seitansaiMembers: Optional[List[str]] = None
    isBirthday: Optional[bool] = False

    class Config:
        populate_by_name = True


class PaginationMeta(BaseModel):
    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class EventPaginationResponse(BaseModel):
    data: List[Event]
    meta: PaginationMeta
