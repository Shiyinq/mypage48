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
    imageUrl_medium: Optional[str] = None
    imageUrl_small: Optional[str] = None
    blurHash: Optional[str] = None
    totalMembers: int = 0
    seitansaiMembers: Optional[List[str]] = None
    graduationMembers: Optional[List[str]] = None
    setlistId: Optional[str] = None
    team: Optional[EventTeam] = None

    class Config:
        populate_by_name = True


class CalendarEvent(BaseModel):
    id: Optional[str] = None
    title: str
    date: datetime
    url: str
    label: Optional[str] = None
    type: Optional[str] = None
    setlistId: Optional[str] = None
    seitansaiMembers: Optional[List[str]] = None
    graduationMembers: Optional[List[str]] = None
    isBirthday: Optional[bool] = False

    class Config:
        populate_by_name = True


class PaginationMeta(BaseModel):
    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class MemberEventStats(BaseModel):
    total_shows: int = 0
    top_setlist_id: Optional[str] = None
    top_setlist_title: Optional[str] = None
    top_setlist_count: int = 0
    unique_setlists: int = 0


class EventPaginationResponse(BaseModel):
    data: List[Event]
    meta: PaginationMeta


class EventMember(BaseModel):
    id: str
    name: str
    img: Optional[str] = None
    img_medium: Optional[str] = None
    img_small: Optional[str] = None
    blurHash: Optional[str] = None
    member_type: Optional[str] = None
    nickname: Optional[str] = None


class EventDetail(Event):
    raw_data: Optional[dict] = None
    members: Optional[List[EventMember]] = None
