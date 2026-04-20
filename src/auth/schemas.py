from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator

from src.auth.http_exceptions import PasswordPolicyViolation, PasswordsNotMatch
from src.utils import validate_password_strength


class OshiSocials(BaseModel):
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    threads: Optional[str] = None
    showroom: Optional[str] = None
    idn_app: Optional[str] = None


class OshiShowResponse(BaseModel):
    title: str
    date: datetime
    url: Optional[str] = None


class OshiResponse(BaseModel):
    name: str = "Unknown"
    nickname: str = "-"
    generation: str = "-"
    profilePicture: str = (
        "https://upload.wikimedia.org/wikipedia/commons/8/82/JKT48.svg"
    )
    profilePicture_medium: Optional[str] = None
    profilePicture_small: Optional[str] = None
    catchphrase: str = "-"
    socials: Optional[OshiSocials] = None
    totalShows: int = 0
    upcomingSchedule: List[OshiShowResponse] = []
    pastSchedule: List[OshiShowResponse] = []


class UserLoginBase(BaseModel):
    userId: str
    profilePicture: str | None = None
    profilePicture_medium: str | None = None
    profilePicture_small: str | None = None
    name: str
    email: str
    username: str
    memberId: str | None = None
    oshiId: str | None = None
    ofcStatus: str | None = None
    isPublic: bool = False
    publicYear: int | None = None
    isAdmin: bool = False

    @field_validator("oshiId", mode="before")
    @classmethod
    def allow_int_oshi_id(cls, v):
        if v is None:
            return None
        return str(v)


class UserLogin(UserLoginBase):
    password: Optional[str] = None
    isEmailVerified: bool = False
    failedLoginAttempts: int = 0
    isAccountLocked: bool = False
    accountLockedUntil: Optional[datetime] = None


class UserCurrent(UserLoginBase):
    oshi: Optional[OshiResponse] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class RefreshTokenData(BaseModel):
    userId: str
    hashRefreshToken: str
    device: str
    ip: str
    browser: str
    createdAt: Optional[datetime] = None
    lastUsedAt: Optional[datetime] = None


class LoginHistory(BaseModel):
    userId: str
    device: str
    ip: str
    browser: str
    loginAt: datetime
    userAgentRaw: Optional[str] = None


# Email Verification Schemas
class EmailVerificationRequest(BaseModel):
    email: str


class EmailVerificationResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyEmailResponse(BaseModel):
    message: str


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetResponse(BaseModel):
    message: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def verify_password_match(self):
        if self.new_password != self.confirm_password:
            raise PasswordsNotMatch()

        if not validate_password_strength(self.new_password):
            raise PasswordPolicyViolation()

        return self


class PasswordResetConfirmResponse(BaseModel):
    message: str


# Security Schemas
class SecurityStatus(BaseModel):
    isEmailVerified: bool
    failedLoginAttempts: int
    isAccountLocked: bool
    accountLockedUntil: Optional[datetime] = None
    lastLoginAt: Optional[str] = None


class VerificationToken(BaseModel):
    userId: str
    email: str
    token: str
    tokenType: str  # 'email_verification' or 'password_reset'
    expiresAt: datetime
    createdAt: datetime


class ResendVerificationRequest(BaseModel):
    email: str


class ResendVerificationResponse(BaseModel):
    message: str


class LogoutResponse(BaseModel):
    message: str
