from datetime import datetime
from typing import Annotated, List, Optional, Union

from pydantic import BaseModel, BeforeValidator, Field, field_validator

from src.utils import cleanse_image_markdown, cleanse_image_url

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


class TicketTwoShotBase(BaseModel):
    member_name: str
    type: str = "Roulette"  # 'Roulette' | 'Birthday'
    price: float
    imageUrl: Optional[str] = None
    imageUrl_medium: Optional[str] = None
    imageUrl_small: Optional[str] = None
    blurHash: Optional[str] = None


class TicketTwoShot(TicketTwoShotBase):
    @field_validator("imageUrl")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        return cleanse_image_url(v)


class TicketBase(BaseModel):
    ticket_id: str
    event: TicketEvent
    seat: TicketSeat
    price: float
    currency: str = "IDR"
    rules: TicketRules = Field(default_factory=TicketRules)
    imageUrl: Optional[str] = None
    imageUrl_medium: Optional[str] = None
    imageUrl_small: Optional[str] = None
    blurHash: Optional[str] = None
    notes: Optional[str] = None


class TicketCreateRequest(TicketBase):
    two_shot: Optional[TicketTwoShot] = None

    @field_validator("imageUrl")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        return cleanse_image_url(v)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        return cleanse_image_markdown(v)


class TicketUpdateRequest(BaseModel):
    ticket_id: Optional[str] = None
    event: Optional[TicketEvent] = None
    seat: Optional[TicketSeat] = None
    price: Optional[float] = None
    rules: Optional[TicketRules] = None
    imageUrl: Optional[str] = None
    blurHash: Optional[str] = None
    notes: Optional[str] = None
    two_shot: Optional[TicketTwoShot] = None

    @field_validator("imageUrl")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        return cleanse_image_url(v)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        return cleanse_image_markdown(v)


class TicketInDB(TicketBase):
    user_id: str
    created_at: datetime
    updated_at: datetime
    two_shot: Optional[TicketTwoShotBase] = None


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
