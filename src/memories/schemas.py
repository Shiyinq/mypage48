from enum import Enum
from typing import Optional

from pydantic import BaseModel

from src.tickets.schemas import PaginationMeta


class MemoryType(str, Enum):
    TICKET = "TICKET"
    TWO_SHOT = "2SHOT"
    ALL = "ALL"


class MemoryItem(BaseModel):
    """A single memory item (ticket image or 2-shot image)."""

    uniqueId: str
    type: MemoryType
    imageUrl: str
    date: str
    time: str
    title: str
    subtitle: str
    notes: Optional[str] = None
    # Additional fields needed by frontend MemoryCard for 2SHOT display
    eventTitle: Optional[str] = None  # Original event title for 2SHOT
    twoShotMemberName: Optional[str] = None  # Member name for 2SHOT


class MemoriesPaginationResponse(BaseModel):
    """Paginated response for memories endpoint."""

    data: list[MemoryItem]
    meta: PaginationMeta


class TopTwoShotMember(BaseModel):
    name: str
    count: int
    spend: int
    lastDate: str
    image: Optional[str] = None


class TopTwoShotResponse(BaseModel):
    ranking: list[TopTwoShotMember]
    totalTwoShotSpend: int
    totalTwoShotCount: int
