from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.tickets.schemas import PaginationMeta


class SocialMedia(BaseModel):
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    threads: Optional[str] = None
    showroom: Optional[str] = None
    idn_app: Optional[str] = None


class MemberBase(BaseModel):
    id: int
    name: str
    nickname: str
    generation: Optional[str] = None
    jiko: Optional[str] = None
    active: bool = True
    href: Optional[str] = None
    img: Optional[str] = None
    birthdate: Optional[str] = None
    bloodType: Optional[str] = None
    horoscope: Optional[str] = None
    height: Optional[str] = None
    socials: Optional[SocialMedia] = None


class MemberCreate(MemberBase):
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)


class MemberResponse(MemberBase):
    pass


class MemberListResponse(BaseModel):
    data: List[MemberResponse]
    meta: PaginationMeta


class MemberDetailResponse(BaseModel):
    member: MemberResponse
    detail: Optional[str] = None


class MemberSeedResponse(BaseModel):
    message: str
    count: int


class MemberCreateRequest(BaseModel):
    """Request schema for creating a member"""

    name: str
    nickname: str
    generation: Optional[str] = None
    jiko: Optional[str] = None
    active: bool = True
    href: Optional[str] = None
    img: Optional[str] = None
    birthdate: Optional[str] = None
    bloodType: Optional[str] = None
    horoscope: Optional[str] = None
    height: Optional[str] = None
    socials: Optional[SocialMedia] = None


class MemberUpdateRequest(BaseModel):
    """Request schema for updating a member (all fields optional)"""

    name: Optional[str] = None
    nickname: Optional[str] = None
    generation: Optional[str] = None
    jiko: Optional[str] = None
    active: Optional[bool] = None
    href: Optional[str] = None
    img: Optional[str] = None
    birthdate: Optional[str] = None
    bloodType: Optional[str] = None
    horoscope: Optional[str] = None
    height: Optional[str] = None
    socials: Optional[SocialMedia] = None


class MessageResponse(BaseModel):
    """Simple message response for delete operations"""

    message: str
