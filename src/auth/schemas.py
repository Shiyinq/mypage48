from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from src.auth.http_exceptions import PasswordPolicyViolation, PasswordsNotMatch
from src.utils import validate_password_strength


class UserLoginBase(BaseModel):
    userId: str
    profilePicture: str | None = None
    name: str
    email: str
    username: str


class UserLogin(UserLoginBase):
    password: Optional[str] = None
    isEmailVerified: bool = False
    failedLoginAttempts: int = 0
    isAccountLocked: bool = False
    accountLockedUntil: Optional[datetime] = None


class UserCurrent(UserLoginBase):
    pass


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
