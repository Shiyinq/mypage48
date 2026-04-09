from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from src.achievements.schemas import RankInfo
from src.auth.schemas import OshiResponse
from src.users.constants import ErrorCode, Info
from src.utils import cleanse_image_url, validate_password_strength


class UserCreateRequest(BaseModel):
    """
    Request schema for user registration.
    Only contains fields that users are allowed to input.
    This prevents Mass Assignment attacks.
    """

    fullName: str = Field(max_length=100)
    username: str = Field(max_length=50)
    email: EmailStr
    password: str
    confirmPassword: str

    @model_validator(mode="after")
    def verify_password_match(self):
        if self.password != self.confirmPassword:
            raise ValueError(ErrorCode.PASSWORD_MISMATCH)

        if not validate_password_strength(self.password):
            raise ValueError(ErrorCode.PASSWORD_RULES)

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "fullName": "John Doe",
                "username": "johndoe",
                "email": "user@example.com",
                "password": "SecurePass123!",
                "confirmPassword": "SecurePass123!",
            }
        }


class ProviderUserCreateRequest(BaseModel):
    """
    Request schema for OAuth provider user creation.
    Only contains fields from OAuth provider response.
    """

    profilePicture: Optional[str] = Field(default=None)
    name: str = Field(max_length=100)
    username: str = Field(max_length=50)
    email: EmailStr
    provider: str

    @field_validator("profilePicture")
    @classmethod
    def validate_profile_picture(cls, v: Optional[str]) -> Optional[str]:
        return cleanse_image_url(v)


class UserInDB(BaseModel):
    """
    Schema for user data stored in database.
    All sensitive fields are set by the service layer, not from user input.
    """

    userId: str = Field(default_factory=lambda: str(uuid4()))
    profilePicture: Optional[str] = Field(default=None)
    name: str = Field(max_length=100)  # Stores fullName or OAuth name
    memberId: Optional[str] = Field(
        max_length=20, default=None
    )  # Optional for OAuth users
    oshiId: Optional[str] = Field(default=None)
    username: str = Field(max_length=50)
    email: EmailStr
    ofcStatus: str = Field(default="Active")
    password: Optional[str] = Field(default=None)
    provider: Optional[str] = Field(default=None)
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    isEmailVerified: bool = Field(default=False)
    isPublic: bool = Field(default=False)
    publicYear: Optional[int] = Field(default=None)  # None = All Years
    failedLoginAttempts: int = Field(default=0)
    isAccountLocked: bool = Field(default=False)
    accountLockedUntil: Optional[datetime] = Field(default=None)

    @field_validator("oshiId", mode="before")
    @classmethod
    def allow_int_oshi_id(cls, v):
        if v is None:
            return None
        return str(v)


class UserCreateResponse(BaseModel):
    detail: str


class UserCreatedWithEmail(UserCreateResponse):
    detail: str = Info.USER_CREATED_WITH_EMAIL


class UserCreated(UserCreateResponse):
    detail: str = Info.USER_CREATED


class PublicShowEntry(BaseModel):
    title: str
    date: datetime
    type: str  # 'Theater' or '2-Shot'


class UserStats(BaseModel):
    totalShows: int
    totalTwoShots: int
    totalSpent: float
    topRow: Optional[str] = None
    topShow: Optional[str] = None
    topRowCount: Optional[int] = 0
    topShowCount: Optional[int] = 0
    rowCounts: Optional[dict] = None
    seatCounts: Optional[dict] = None
    recentActivity: Optional[list[PublicShowEntry]] = None


class PublicUserResponse(BaseModel):
    name: str
    username: str
    profilePicture: Optional[str] = None
    oshi: Optional[OshiResponse] = None
    createdAt: datetime
    publicYear: Optional[int] = None
    stats: Optional[UserStats] = None


class UpdateProfilePictureRequest(BaseModel):
    profilePicture: str

    @field_validator("profilePicture")
    @classmethod
    def validate_profile_picture(cls, v: str) -> str:
        return cleanse_image_url(v)


class UpdateOshiRequest(BaseModel):
    oshiId: str

    @field_validator("oshiId", mode="before")
    @classmethod
    def allow_int_oshi_id(cls, v):
        if v is None:
            return None
        return str(v)


class UpdatePublicStatusRequest(BaseModel):
    isPublic: bool
    publicYear: Optional[int] = None  # None means "All Time"


class MessageResponse(BaseModel):
    detail: str


class ProfileStats(BaseModel):
    """Quick stats for profile page."""

    totalShows: int
    totalAchievements: int
    oshiMeetings: int = 0


class ProfileRecentActivity(BaseModel):
    """Recent activity entry for profile page."""

    ticketId: str
    title: str
    date: str
    section: str
    number: str
    hasTwoShot: bool
    twoShotMember: Optional[str] = None


class OshiTwoShotCounts(BaseModel):
    """2-shot counts with user's oshi."""

    roulette: int
    birthday: int


class ProfileFullResponse(BaseModel):
    """Complete profile response with all sections."""

    profile: dict  # UserCurrent as dict to avoid circular import
    oshi: Optional[OshiResponse] = None
    rank: RankInfo
    stats: ProfileStats
    oshiTwoShots: OshiTwoShotCounts
    recentActivity: list[ProfileRecentActivity]


# Admin User List Schemas
class UserListItem(BaseModel):
    """User item for admin list view."""

    userId: str
    name: str
    username: str
    email: str
    profilePicture: Optional[str] = None
    isAdmin: bool = False
    isEmailVerified: bool = False
    isAccountLocked: bool = False
    createdAt: datetime


class UserPaginationMeta(BaseModel):
    """Pagination metadata for user list."""

    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class UserListResponse(BaseModel):
    """Paginated user list response for admin."""

    data: list[UserListItem]
    meta: UserPaginationMeta
