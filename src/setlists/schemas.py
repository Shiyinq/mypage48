from typing import List, Optional

from pydantic import BaseModel


class SetlistBase(BaseModel):
    setlistId: str
    imageUrl: str
    title: str
    titleJapanese: Optional[str] = None
    description: str
    type: str  # "setlist" or "event"
    active: bool = False
    songs: Optional[List[str]] = []


class WatchedStats(BaseModel):
    """User-specific watch statistics for a setlist"""

    count: int = 0  # Number of times user has watched this show
    percentage: float = 0.0  # Percentage relative to max attendance
    isMostWatched: bool = False  # True if this is the most watched show


class SetlistResponse(SetlistBase):
    pass  # No additional fields for base response


class SetlistWithStats(SetlistBase):
    """Setlist response with user-specific statistics"""

    watched: WatchedStats


class SetlistListResponse(BaseModel):
    total: int
    maxAttendance: int  # Maximum ticket count across all shows
    setlists: List[SetlistWithStats]


class SetlistSeedResponse(BaseModel):
    message: str
    count: int


# ---- Detail response with tickets ----


class TicketEvent(BaseModel):
    """Event info from a ticket"""

    title: str
    date: str
    time: str


class TicketSeat(BaseModel):
    """Seat info from a ticket"""

    section: str
    number: int


class TicketItem(BaseModel):
    """Ticket summary for setlist detail"""

    ticketId: str
    event: TicketEvent
    seat: TicketSeat
    price: int
    notes: Optional[str] = None


class SetlistDetailStats(BaseModel):
    """Computed statistics for setlist detail"""

    totalAttendance: int
    totalSpent: int
    avgPrice: float
    topRow: Optional[str] = None
    firstDate: Optional[str] = None
    lastDate: Optional[str] = None


class SetlistDetailResponse(SetlistBase):
    """Setlist detail with user tickets and computed stats"""

    watched: WatchedStats
    stats: SetlistDetailStats
    tickets: List[TicketItem]
