import asyncio
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Union

from jose import JWTError, jwt

from src.auth.email_service import EmailService
from src.auth.exceptions import IncorrectCredentialsError, InvalidJWTTokenError
from src.auth.repository import AuthRepository
from src.auth.schemas import TokenData, UserLogin
from src.auth.security_service import SecurityService
from src.config import Settings
from src.logging_config import create_logger
from src.users.exceptions import AccountLocked, EmailNotVerified
from src.users.repository import UserRepository
from src.utils import hash_token

logger = create_logger("auth_service", __name__)


class AuthService:
    def __init__(
        self,
        auth_repo: AuthRepository,
        user_repo: UserRepository,
        security_service: SecurityService,
        email_service: EmailService,
        config: Settings,
    ):
        self.auth_repo = auth_repo
        self.user_repo = user_repo
        self.security_service = security_service
        self.email_service = email_service
        self.config = config

    async def verify_password(self, plain_password, hashed_password) -> str:
        return await asyncio.to_thread(
            self.security_service.verify_password, plain_password, hashed_password
        )

    async def get_password_hash(self, password) -> str:
        return await asyncio.to_thread(
            self.security_service.get_password_hash, password
        )

    def create_access_token(
        self, data: dict, expires_delta: timedelta | None = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.config.access_token_expire_minutes
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.config.secret_key, algorithm=self.config.algorithm
        )
        return encoded_jwt

    def verify_access_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(
                token, self.config.secret_key, algorithms=[self.config.algorithm]
            )
            username: str = payload.get("sub")
            if username is None:
                logger.warning("Token does not contain sub/username")
                raise InvalidJWTTokenError()
            token_data = TokenData(username=username)
            return token_data
        except JWTError as e:
            logger.exception(f"JWTError: {str(e)}")
            raise InvalidJWTTokenError()

    async def get_user(self, username_or_email: str) -> Optional[UserLogin]:
        username_or_email = username_or_email.lower()
        query = {
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email},
                {"userId": username_or_email},
            ]
        }
        user = await self.user_repo.find_one(query)
        if user:
            return UserLogin(**user)
        return None

    async def authenticate_user(
        self, username_or_email: str, password: str = None, provider: str = None
    ) -> Union[UserLogin, bool]:
        user = await self.get_user(username_or_email)

        # For provider-based auth, skip password verification
        if provider is not None:
            if not user:
                return False
            return user

        # Mitigate timing attacks by always performing verification for password-based auth
        is_valid_password = False
        if user and user.password:
            is_valid_password = await self.verify_password(password, user.password)
        else:
            # Fake verification to prevent timing attacks
            fake_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
            await self.verify_password(password or "dummy", fake_hash)

        if not user:
            raise IncorrectCredentialsError()

        # Check account lock status
        lock_status = await self.security_service.check_account_lock_status(user.userId)
        if lock_status["is_locked"]:
            raise AccountLocked()

        if not user.isEmailVerified:
            raise EmailNotVerified()

        if not is_valid_password:
            # Handle failed login
            await self.security_service.handle_failed_login(
                user.userId, user.email, user.username
            )
            raise IncorrectCredentialsError()

        await self.security_service.reset_failed_login_attempts(user.userId)
        return user

    def extract_user_provider(self, user) -> Dict[str, str]:
        return {
            "profilePicture": user.picture,
            "name": user.display_name,
            "username": user.email,
            "email": user.email,
            "provider": user.provider,
        }

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(64)

    def hash_token(self, token: str) -> str:
        return hash_token(token)

    async def save_refresh_token(
        self, user_id: str, refresh_token: str, device: str, ip: str, browser: str
    ):
        data = {
            "userId": user_id,
            "hashRefreshToken": refresh_token,
            "device": device,
            "ip": ip,
            "browser": browser,
            "createdAt": datetime.now(timezone.utc),
            "lastUsedAt": datetime.now(timezone.utc),
        }
        await self.auth_repo.insert_refresh_token(data)

    async def get_refresh_token(self, token: str) -> Optional[dict]:
        return await self.auth_repo.find_refresh_token(token)

    async def update_refresh_token_last_used(self, token: str):
        await self.auth_repo.update_refresh_token_last_used(token)

    async def delete_refresh_token(self, token: str):
        await self.auth_repo.delete_refresh_token(token)

    async def save_login_history(
        self,
        user_id: str,
        device: str,
        ip: str,
        browser: str,
        user_agent_raw: Optional[str] = None,
    ):
        data = {
            "userId": user_id,
            "device": device,
            "ip": ip,
            "browser": browser,
            "loginAt": datetime.now(timezone.utc),
            "userAgentRaw": user_agent_raw,
        }
        await self.auth_repo.insert_login_history(data)

    async def get_last_login_history(self, user_id: str) -> Optional[dict]:
        return await self.auth_repo.find_last_login_history(user_id)

    async def register_refresh_token_activity(
        self, user_id: str, device: str, ip: str, browser: str, user_agent: str
    ) -> str:
        refresh_token = self.create_refresh_token()
        hash_refresh_token = hash_token(refresh_token)
        await self.save_refresh_token(user_id, hash_refresh_token, device, ip, browser)
        await self.save_login_history(
            user_id, device, ip, browser, user_agent_raw=user_agent
        )
        return refresh_token

    async def create_email_verification_token(self, user_id: str) -> str:
        """Create and save email verification token"""
        token = await self.security_service.create_and_save_token(
            user_id,
            "email_verification",
            self.config.email_verification_expire_hours,
        )
        return token

    async def verify_email(self, token: str) -> bool:
        """Verify email with token"""
        token_hash = hash_token(token)
        user_id = await self.security_service.verify_email_token(token_hash)
        return user_id is not None

    async def create_password_reset_token(
        self, email: str
    ) -> Optional[tuple[str, str, str]]:
        """
        Create and save password reset token.
        Returns (token, username, email) if user exists, else None.
        """
        user = await self.get_user(email)
        if not user:
            return None  # Don't reveal if email not exists

        token = await self.security_service.create_and_save_token(
            user.userId,
            "password_reset",
            self.config.password_reset_expire_hours,
        )

        await self.email_service.send_password_reset(user.email, token, user.username)

        return token, user.username, user.email

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token"""
        token_hash = hash_token(token)
        token_data = await self.security_service.verify_token(
            token_hash, "password_reset"
        )
        if not token_data:
            return False

        # Update password using userId
        hashed_password = await self.get_password_hash(new_password)

        await self.user_repo.update_one(
            {"userId": token_data["userId"]}, {"$set": {"password": hashed_password}}
        )

        await self.security_service.delete_token(token_hash, "password_reset")

        user = await self.user_repo.find_one({"userId": token_data["userId"]})
        if user:
            await self.security_service.reset_failed_login_attempts(user["userId"])
            await self.security_service.unlock_account(user["userId"])

        return True

    async def resend_verification_email(
        self, email: str
    ) -> Optional[tuple[str, str, str]]:
        """
        Resend verification email.
        Returns (token, username, email) if eligible, else None.
        """
        user = await self.get_user(email)
        if not user:
            return None

        if user.isEmailVerified:
            return None  # Already verified

        token = await self.create_email_verification_token(user.userId)

        await self.email_service.send_email_verification(
            user.email, token, user.username
        )

        return token, user.username, user.email
