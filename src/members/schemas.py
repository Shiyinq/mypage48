from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from src.tickets.schemas import PaginationMeta
from src.utils import validate_image_path


class SocialMedia(BaseModel):
    twitter: Optional[str] = Field(default=None, max_length=200)
    instagram: Optional[str] = Field(default=None, max_length=200)
    tiktok: Optional[str] = Field(default=None, max_length=200)
    threads: Optional[str] = Field(default=None, max_length=200)
    showroom: Optional[str] = Field(default=None, max_length=200)
    idn_app: Optional[str] = Field(default=None, max_length=200)


class MemberBase(BaseModel):
    id: str
    name: str
    nickname: Optional[str] = None
    generation: Optional[str] = None
    jiko: Optional[str] = None
    active: bool = True
    href: Optional[str] = None
    img: Optional[str] = None
    img_medium: Optional[str] = None
    img_small: Optional[str] = None
    blurHash: Optional[str] = None
    birthdate: Optional[str] = None
    bloodType: Optional[str] = None
    horoscope: Optional[str] = None
    height: Optional[str] = None
    socials: Optional[SocialMedia] = None
    member_type: Optional[str] = "JKT48"
    member_code: Optional[str] = None

    @field_validator(
        "nickname",
        "generation",
        "jiko",
        "birthdate",
        "bloodType",
        "horoscope",
        "height",
        "img",
        "member_type",
        "member_code",
        mode="before",
    )
    @classmethod
    def parse_empty_string(cls, v, info: ValidationInfo):
        if v is None:
            if info.field_name == "img":
                return "https://placehold.co/600x800?text=No+Photo"
            return "-"
        return v

    @field_validator("socials", mode="before")
    @classmethod
    def parse_socials(cls, v):
        if v is None:
            return {}
        return v


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

    name: str = Field(max_length=100)
    nickname: str = Field(max_length=50)
    generation: Optional[str] = Field(default=None, max_length=50)
    jiko: Optional[str] = Field(default=None, max_length=500)
    active: bool = True
    href: Optional[str] = Field(default=None, max_length=200)
    img: Optional[str] = Field(default=None, max_length=100)
    blurHash: Optional[str] = Field(default=None, max_length=100)
    birthdate: Optional[str] = Field(default=None, max_length=50)
    bloodType: Optional[str] = Field(default=None, max_length=10)
    horoscope: Optional[str] = Field(default=None, max_length=50)
    height: Optional[str] = Field(default=None, max_length=20)
    socials: Optional[SocialMedia] = None
    member_type: Optional[str] = Field(default="JKT48", max_length=50)
    member_code: Optional[str] = Field(default=None, max_length=50)

    @field_validator("img")
    @classmethod
    def validate_img(cls, v: Optional[str]) -> Optional[str]:
        return validate_image_path(v, "media/jkt48-member/", "Member")


class MemberUpdateRequest(BaseModel):
    """Request schema for updating a member (all fields optional)"""

    name: Optional[str] = Field(default=None, max_length=100)
    nickname: Optional[str] = Field(default=None, max_length=50)
    generation: Optional[str] = Field(default=None, max_length=50)
    jiko: Optional[str] = Field(default=None, max_length=500)
    active: Optional[bool] = None
    href: Optional[str] = Field(default=None, max_length=200)
    img: Optional[str] = Field(default=None, max_length=100)
    blurHash: Optional[str] = Field(default=None, max_length=100)
    birthdate: Optional[str] = Field(default=None, max_length=50)
    bloodType: Optional[str] = Field(default=None, max_length=10)
    horoscope: Optional[str] = Field(default=None, max_length=50)
    height: Optional[str] = Field(default=None, max_length=20)
    socials: Optional[SocialMedia] = None
    member_type: Optional[str] = Field(default=None, max_length=50)
    member_code: Optional[str] = Field(default=None, max_length=50)

    @field_validator("img")
    @classmethod
    def validate_img(cls, v: Optional[str]) -> Optional[str]:
        return validate_image_path(v, "media/jkt48-member/", "Member")


class MessageResponse(BaseModel):
    """Simple message response for delete operations"""

    message: str


class BirthdayResponse(BaseModel):
    """Response schema for member birthday"""

    id: str
    name: str
    active: bool
    img: Optional[str] = None
    img_medium: Optional[str] = None
    img_small: Optional[str] = None
    blurHash: Optional[str] = None
    birthdate: str
    days_until: int
    age: int
    member_type: Optional[str] = "JKT48"
