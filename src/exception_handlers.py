from fastapi import Request
from fastapi.responses import JSONResponse

from src.api_keys.exceptions import (
    APIKeyCreationError,
    APIKeyDeletionError,
    APIKeyNotFoundError,
)
from src.api_keys.http_exceptions import (
    APIKeyCreateError,
    APIKeyDeleteError,
    APIKeyNotFound,
)
from src.auth.exceptions import (
    IncorrectCredentialsError,
    InvalidJWTTokenError,
    InvalidRefreshTokenError,
    PasswordPolicyViolationError,
    PasswordResetTokenInvalidError,
    PasswordsDoNotMatchError,
    RefreshTokenExpiredError,
    SuspiciousActivityError,
    VerificationTokenInvalidError,
)
from src.auth.http_exceptions import (
    AccountLocked,
    EmailNotVerified,
    IncorrectEmailOrPassword,
    InvalidJWTToken,
    InvalidRefreshToken,
    PasswordPolicyViolation,
    PasswordResetTokenInvalid,
    PasswordsNotMatch,
    RefreshTokenExpired,
    SuspiciousActivity,
    VerificationTokenInvalid,
)
from src.exceptions import DomainException
from src.http_exceptions import DetailedHTTPException
from src.logging_config import create_logger
from src.users.exceptions import AccountLocked as DomainAccountLocked
from src.users.exceptions import EmailAlreadyExistsError
from src.users.exceptions import EmailNotVerified as DomainEmailNotVerified
from src.users.exceptions import (
    ProviderUserCreationError,
    UserCreationError,
    UsernameAlreadyExistsError,
)
from src.users.http_exceptions import EmailTaken, ServerError, UsernameTaken

logger = create_logger("exceptions", __name__)


async def domain_exception_handler(request: Request, exc: DomainException):
    logger.warning(
        f"Domain exception occurred: type={type(exc).__name__}, message={str(exc)}, path={request.url.path}"
    )

    if isinstance(exc, UsernameAlreadyExistsError):
        return await detailed_http_exception_handler(request, UsernameTaken())
    if isinstance(exc, EmailAlreadyExistsError):
        return await detailed_http_exception_handler(request, EmailTaken())
    if isinstance(exc, (UserCreationError, ProviderUserCreationError)):
        logger.error(f"Critical domain error: {str(exc)}")
        return await detailed_http_exception_handler(request, ServerError())

    if isinstance(exc, IncorrectCredentialsError):
        return await detailed_http_exception_handler(
            request, IncorrectEmailOrPassword()
        )
    if isinstance(exc, InvalidJWTTokenError):
        return await detailed_http_exception_handler(request, InvalidJWTToken())
    if isinstance(exc, InvalidRefreshTokenError):
        return await detailed_http_exception_handler(request, InvalidRefreshToken())
    if isinstance(exc, RefreshTokenExpiredError):
        return await detailed_http_exception_handler(request, RefreshTokenExpired())
    if isinstance(exc, SuspiciousActivityError):
        logger.error(f"Suspicious activity detected: {str(exc)}")
        return await detailed_http_exception_handler(request, SuspiciousActivity())
    if isinstance(exc, VerificationTokenInvalidError):
        return await detailed_http_exception_handler(
            request, VerificationTokenInvalid()
        )
    if isinstance(exc, PasswordResetTokenInvalidError):
        return await detailed_http_exception_handler(
            request, PasswordResetTokenInvalid()
        )
    if isinstance(exc, PasswordsDoNotMatchError):
        return await detailed_http_exception_handler(request, PasswordsNotMatch())
    if isinstance(exc, PasswordPolicyViolationError):
        return await detailed_http_exception_handler(request, PasswordPolicyViolation())

    if isinstance(exc, DomainAccountLocked):
        return await detailed_http_exception_handler(request, AccountLocked())
    if isinstance(exc, DomainEmailNotVerified):
        return await detailed_http_exception_handler(request, EmailNotVerified())

    if isinstance(exc, APIKeyCreationError):
        return await detailed_http_exception_handler(request, APIKeyCreateError())
    if isinstance(exc, APIKeyDeletionError):
        return await detailed_http_exception_handler(request, APIKeyDeleteError())
    if isinstance(exc, APIKeyNotFoundError):
        return await detailed_http_exception_handler(request, APIKeyNotFound())

    error_msg = str(exc)
    if (
        "password" in error_msg.lower()
        or "secret" in error_msg.lower()
        or "key" in error_msg.lower()
    ):
        error_msg = "Error details redacted for security"

    logger.error(
        f"Unhandled domain/unexpected exception: {type(exc).__name__}: {error_msg}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


async def detailed_http_exception_handler(request: Request, exc: DetailedHTTPException):
    return JSONResponse(
        status_code=exc.STATUS_CODE,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )
