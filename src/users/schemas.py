from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field, model_validator

from src.users.constants import Info
from src.users.http_exceptions import PasswordNotMatch, PasswordRules
from src.utils import validate_password_strength


class UserCreateRequest(BaseModel):
    """
    Request schema for user registration.
    Only contains fields that users are allowed to input.
    This prevents Mass Assignment attacks.
    """

    name: str = Field(max_length=20)
    username: str = Field(max_length=50)
    email: EmailStr
    password: str
    confirmPassword: str

    @model_validator(mode="after")
    def verify_password_match(self):
        if self.password != self.confirmPassword:
            raise PasswordNotMatch

        if not validate_password_strength(self.password):
            raise PasswordRules

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
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

    profilePicture: Optional[str] = Field(max_length=255, default=None)
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
    profilePicture: Optional[str] = Field(max_length=255, default=None)
    name: str = Field(max_length=100)
    username: str = Field(max_length=50)
    email: EmailStr
    password: Optional[str] = Field(default=None)
    provider: Optional[str] = Field(default=None)
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    isEmailVerified: bool = Field(default=False)
    failedLoginAttempts: int = Field(default=0)
    isAccountLocked: bool = Field(default=False)
    accountLockedUntil: Optional[datetime] = Field(default=None)


class UserCreateResponse(BaseModel):
    detail: str


class UserCreatedWithEmail(UserCreateResponse):
    detail: str = Info.USER_CREATED_WITH_EMAIL


class UserCreated(UserCreateResponse):
    detail: str = Info.USER_CREATED
