from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from src.utils import validate_image_path


class SetlistBase(BaseModel):
    setlistId: str
    imageUrl: str
    imageUrl_medium: Optional[str] = None
    imageUrl_small: Optional[str] = None
    blurHash: Optional[str] = None
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


class TwoShotHistoryItem(BaseModel):
    name: str
    count: int
    imageUrl: Optional[str] = None
    imageUrl_medium: Optional[str] = None
    imageUrl_small: Optional[str] = None
    blurHash: Optional[str] = None


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
    topRowCount: int = 0
    firstDate: Optional[str] = None
    lastDate: Optional[str] = None
    firstSeat: Optional[str] = None
    lastSeat: Optional[str] = None
    total2Shot: int = 0


class SetlistDetailResponse(SetlistBase):
    """Setlist detail with user tickets and computed stats"""

    watched: WatchedStats
    stats: SetlistDetailStats
    tickets: List[TicketItem]
    twoShots: List[TwoShotHistoryItem] = Field(default_factory=list)


class SetlistCreateRequest(BaseModel):
    """Request schema for creating a setlist"""

    imageUrl: str = Field(max_length=100)
    blurHash: Optional[str] = Field(default=None, max_length=100)
    title: str = Field(max_length=100)
    titleJapanese: Optional[str] = Field(default=None, max_length=100)
    description: str = Field(max_length=1000)
    type: Literal["setlist", "event"]
    active: bool = False
    songs: Optional[List[str]] = []

    @field_validator("imageUrl")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        return validate_image_path(v, "media/setlists/", "Setlist")


class SetlistUpdateRequest(BaseModel):
    """Request schema for updating a setlist (all fields optional)"""

    imageUrl: Optional[str] = Field(default=None, max_length=100)
    blurHash: Optional[str] = Field(default=None, max_length=100)
    title: Optional[str] = Field(default=None, max_length=100)
    titleJapanese: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    type: Optional[Literal["setlist", "event"]] = None
    active: Optional[bool] = None
    songs: Optional[List[str]] = None

    @field_validator("imageUrl")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        return validate_image_path(v, "media/setlists/", "Setlist")


class MessageResponse(BaseModel):
    """Simple message response for delete operations"""

    message: str
