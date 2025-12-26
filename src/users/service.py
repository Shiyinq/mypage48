import asyncio

from pymongo.errors import DuplicateKeyError

from src.auth.email_service import EmailService
from src.auth.security_service import SecurityService
from src.config import Settings
from src.logging_config import create_logger
from src.users.exceptions import (
    EmailAlreadyExistsError,
    ProviderUserCreationError,
    UserCreationError,
    UsernameAlreadyExistsError,
)
from src.users.repository import UserRepository
from src.users.schemas import (
    ProviderUserCreateRequest,
    UserCreated,
    UserCreatedWithEmail,
    UserCreateRequest,
    UserInDB,
)

logger = create_logger("users_service", __name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        security_service: SecurityService,
        email_service: EmailService,
        config: Settings,
    ):
        self.user_repo = user_repo
        self.security_service = security_service
        self.email_service = email_service
        self.config = config

    def _handle_duplicate_key_error(self, dk: DuplicateKeyError):
        """Handle DuplicateKeyError and raise appropriate domain exception."""
        if dk.details and "keyPattern" in dk.details:
            keys = dk.details["keyPattern"]
            if "username" in keys:
                raise UsernameAlreadyExistsError()
            elif "email" in keys:
                raise EmailAlreadyExistsError()

        dk_str = str(dk)
        if "username" in dk_str:
            raise UsernameAlreadyExistsError()
        elif "email" in dk_str:
            raise EmailAlreadyExistsError()

    async def create_user(self, request: UserCreateRequest) -> UserCreated:
        """
        Create a new user from registration request.
        Sensitive fields are set explicitly by this service, not from user input.
        """
        try:
            hashed_password = await asyncio.to_thread(
                self.security_service.get_password_hash, request.password
            )

            user_in_db = UserInDB(
                name=request.name,
                username=request.username.lower(),
                email=request.email.lower(),
                password=hashed_password,
                isEmailVerified=False,
                failedLoginAttempts=0,
                isAccountLocked=False,
                accountLockedUntil=None,
            )

            await self.user_repo.insert_user(user_in_db.model_dump())

            try:
                token = await self.security_service.create_and_save_token(
                    user_in_db.userId,
                    "email_verification",
                    self.config.email_verification_expire_hours,
                )

                await self.email_service.send_email_verification(
                    user_in_db.email, token, user_in_db.username
                )
                return UserCreatedWithEmail()
            except Exception as e:
                logger.warning(
                    f"User created but error sending verification email: {e}"
                )
                return UserCreated()

        except DuplicateKeyError as dk:
            self._handle_duplicate_key_error(dk)
        except (UsernameAlreadyExistsError, EmailAlreadyExistsError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in create_user: {str(e)}")
            raise UserCreationError()

    async def create_user_provider(
        self, request: ProviderUserCreateRequest
    ) -> UserCreated:
        """
        Create a new user from OAuth provider.
        Provider users are automatically email verified.
        """
        try:
            user_in_db = UserInDB(
                profilePicture=request.profilePicture,
                name=request.name,
                username=request.username.lower(),
                email=request.email.lower(),
                password=None,
                provider=request.provider,
                isEmailVerified=True,
                failedLoginAttempts=0,
                isAccountLocked=False,
                accountLockedUntil=None,
            )

            await self.user_repo.insert_user(user_in_db.model_dump())
            return UserCreated()

        except DuplicateKeyError as dk:
            self._handle_duplicate_key_error(dk)
        except (UsernameAlreadyExistsError, EmailAlreadyExistsError):
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in create_user_provider: {str(e)}")
            raise ProviderUserCreationError()
