from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field, model_validator

from src.users.constants import Info, ErrorCode
from src.auth.schemas import OshiResponse
from src.utils import validate_password_strength


class UserCreateRequest(BaseModel):
    """
    Request schema for user registration.
    Only contains fields that users are allowed to input.
    This prevents Mass Assignment attacks.
    """

    fullName: str = Field(max_length=100)
    memberId: str = Field(max_length=20)
    username: str = Field(max_length=50)
    email: EmailStr
    ofcStatus: str = Field(default="Active")  # 'Active' | 'Inactive' | 'Pending'
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
                "memberId": "JKT-1234",
                "username": "johndoe",
                "email": "user@example.com",
                "ofcStatus": "Active",
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


class UserInDB(BaseModel):
    """
    Schema for user data stored in database.
    All sensitive fields are set by the service layer, not from user input.
    """

    userId: str = Field(default_factory=lambda: str(uuid4()))
    profilePicture: Optional[str] = Field(default=None)
    name: str = Field(max_length=100)  # Stores fullName or OAuth name
    memberId: Optional[str] = Field(max_length=20, default=None)  # Optional for OAuth users
    oshiId: Optional[int] = Field(default=None)
    username: str = Field(max_length=50)
    email: EmailStr
    ofcStatus: str = Field(default="Active")
    password: Optional[str] = Field(default=None)
    provider: Optional[str] = Field(default=None)
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    isEmailVerified: bool = Field(default=False)
    isPublic: bool = Field(default=False)
    publicYear: Optional[int] = Field(default=None) # None = All Years
    failedLoginAttempts: int = Field(default=0)
    isAccountLocked: bool = Field(default=False)
    accountLockedUntil: Optional[datetime] = Field(default=None)


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


class UpdateOshiRequest(BaseModel):
    oshiId: int


class UpdatePublicStatusRequest(BaseModel):
    isPublic: bool
    publicYear: Optional[int] = None  # None means "All Time"


class MessageResponse(BaseModel):
    detail: str

