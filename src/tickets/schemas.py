from datetime import datetime
from typing import List, Optional, Union, Annotated
from pydantic import BaseModel, Field, BeforeValidator



PyObjectId = Annotated[str, BeforeValidator(str)]


class TicketEvent(BaseModel):
    title: str
    date: str  # YYYY-MM-DD
    day: str
    time: str
    gate_open: Optional[str] = None
    venue: str = "JKT48 Theater"


class TicketSeat(BaseModel):
    section: str
    number: Union[str, int]


class TicketRules(BaseModel):
    refund_allowed: bool = False
    exchange_allowed: bool = False


class TicketTwoShot(BaseModel):
    member_name: str
    type: str = "Roulette"  # 'Roulette' | 'Birthday'
    price: float
    imageUrl: Optional[str] = None


class TicketCreateRequest(BaseModel):
    ticket_id: str
    event: TicketEvent
    seat: TicketSeat
    price: float
    currency: str = "IDR"
    rules: TicketRules = Field(default_factory=TicketRules)
    imageUrl: Optional[str] = None
    notes: Optional[str] = None
    two_shot: Optional[TicketTwoShot] = None


class TicketUpdateRequest(BaseModel):
    ticket_id: Optional[str] = None
    event: Optional[TicketEvent] = None
    seat: Optional[TicketSeat] = None
    price: Optional[float] = None
    rules: Optional[TicketRules] = None
    imageUrl: Optional[str] = None
    notes: Optional[str] = None
    two_shot: Optional[TicketTwoShot] = None


class TicketInDB(TicketCreateRequest):
    user_id: str
    created_at: datetime
    updated_at: datetime


class TicketResponse(TicketInDB):
    id: PyObjectId = Field(alias="_id")

    class Config:
        populate_by_name = True


class MessageResponse(BaseModel):
    detail: str


class PaginationMeta(BaseModel):
    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class TicketPaginationResponse(BaseModel):
    data: List[TicketResponse]
    meta: PaginationMeta
