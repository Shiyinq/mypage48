from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SocialMedia(BaseModel):
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None


class MemberBase(BaseModel):
    id: int
    name: str
    nickname: str
    href: Optional[str] = None
    img: Optional[str] = None
    birthdate: Optional[str] = None
    bloodType: Optional[str] = None
    horoscope: Optional[str] = None
    height: Optional[str] = None
    socials: Optional[SocialMedia] = None


class MemberCreate(MemberBase):
    generation: Optional[str] = None
    jiko: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)


class MemberResponse(MemberBase):
    generation: Optional[str] = None
    jiko: Optional[str] = None


class MemberListResponse(BaseModel):
    total: int
    members: List[MemberResponse]


class MemberDetailResponse(BaseModel):
    member: MemberResponse
    detail: Optional[str] = None


class MemberSeedResponse(BaseModel):
    message: str
    count: int
