import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from passlib.context import CryptContext

from src.auth.email_service import EmailService
from src.auth.repository import AuthRepository
from src.config import Settings
from src.interfaces import BackgroundTaskRunner
from src.users.repository import UserRepository
from src.utils import hash_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityService:
    def __init__(
        self,
        auth_repo: AuthRepository,
        user_repo: UserRepository,
        email_service: EmailService,
        background_tasks: BackgroundTaskRunner,
        config: Settings,
    ):
        self.auth_repo = auth_repo
        self.user_repo = user_repo
        self.email_service = email_service
        self.background_tasks = background_tasks
        self.config = config

    def verify_password(self, plain_password, hashed_password) -> str:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password) -> str:
        return pwd_context.hash(password)

    def create_token(self) -> str:
        """Create secure token for verification or password reset"""
        return secrets.token_urlsafe(32)

    async def save_token(
        self, user_id: str, token: str, token_type: str, expire_hours: int
    ):
        """Save verification token to general collection"""

        await self.auth_repo.delete_verification_tokens_by_user(user_id, token_type)

        expires_at = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
        data = {
            "userId": user_id,
            "hashToken": token,
            "tokenType": token_type,
            "expiresAt": expires_at,
            "createdAt": datetime.now(timezone.utc),
        }
        await self.auth_repo.insert_verification_token(data)

    async def create_and_save_token(
        self, user_id: str, token_type: str, expire_hours: int
    ) -> str:
        """Create token, hash it, and save to database. Returns plain token."""
        token = self.create_token()
        token_hash = hash_token(token)
        await self.save_token(
            user_id,
            token_hash,
            token_type,
            expire_hours,
        )
        return token

    async def get_token(self, token: str, token_type: str) -> Optional[Dict[str, Any]]:
        """Get token data by type"""
        return await self.auth_repo.find_verification_token(token, token_type)

    async def delete_token(self, token: str, token_type: str):
        """Delete token by type"""
        await self.auth_repo.delete_verification_token(token, token_type)

    async def verify_token(
        self, token: str, token_type: str
    ) -> Optional[Dict[str, Any]]:
        """Verify token and return token data if valid"""
        token_data = await self.get_token(token, token_type)

        if not token_data:
            return None

        # Ensure expires_at has timezone info
        expires_at = token_data["expiresAt"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            await self.delete_token(token, token_type)
            return None

        return token_data

    async def verify_email_token(self, token: str) -> Optional[str]:
        """Verify email verification token"""
        token_data = await self.verify_token(token, "email_verification")

        if not token_data:
            return None

        await self.user_repo.set_email_verified(token_data["userId"])

        await self.delete_token(token, "email_verification")

        return token_data["userId"]

    async def increment_failed_login_attempts(self, user_id: str):
        """Increment failed login attempts count"""
        await self.user_repo.increment_failed_login_attempts(user_id)

    async def reset_failed_login_attempts(self, user_id: str):
        """Reset failed login attempts count"""
        await self.user_repo.reset_failed_login_attempts(user_id)

    async def lock_account(self, user_id: str, duration_minutes: int = 15):
        """Lock account temporarily"""
        locked_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)

        await self.user_repo.lock_account(user_id, locked_until)

    async def unlock_account(self, user_id: str):
        """Unlock account"""
        await self.user_repo.unlock_account(user_id)

    async def check_account_lock_status(self, user_id: str) -> Dict[str, Any]:
        """Check account lock status"""
        user = await self.user_repo.find_one({"userId": user_id})
        if not user:
            return {"is_locked": False, "locked_until": None}

        is_locked = user.get("isAccountLocked", False)
        locked_until = user.get("accountLockedUntil")

        # Auto unlock if expired
        if is_locked and locked_until:
            # Ensure locked_until has timezone info
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)

            if locked_until < datetime.now(timezone.utc):
                await self.unlock_account(user_id)
                return {"is_locked": False, "locked_until": None}

        return {"is_locked": is_locked, "locked_until": locked_until}

    async def handle_failed_login(self, user_id: str, email: str, username: str):
        """Handle failed login with security measures"""

        await self.increment_failed_login_attempts(user_id)

        user = await self.user_repo.find_one({"userId": user_id})
        if (
            user
            and user.get("failedLoginAttempts", 0) >= self.config.max_login_attempts
        ):
            await self.lock_account(user_id, self.config.account_lockout_minutes)

            self.background_tasks.add_task(
                self.email_service.send_account_locked_notification,
                email,
                username,
                self.config.account_lockout_minutes,
            )
