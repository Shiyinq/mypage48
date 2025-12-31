from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
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
    PublicUserNotFoundError,
    UserCreationError,
    UsernameAlreadyExistsError,
)
from src.users.http_exceptions import EmailTaken, PublicUserNotFound, ServerError, UsernameTaken
from src.users.constants import ErrorCode
from src.theater.exceptions import (
    TicketNotFoundError,
    TicketCreationError,
    TicketUpdateError,
    TicketDeletionError,
)
from src.theater.http_exceptions import (
    TicketNotFound,
    TicketCreateError,
    TicketUpdateError as HttpTicketUpdateError,
    TicketDeleteError,
)

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

    if isinstance(exc, PublicUserNotFoundError):
        return await detailed_http_exception_handler(request, PublicUserNotFound())

    if isinstance(exc, TicketNotFoundError):
        return await detailed_http_exception_handler(request, TicketNotFound())
    if isinstance(exc, TicketCreationError):
        return await detailed_http_exception_handler(request, TicketCreateError())
    if isinstance(exc, TicketUpdateError):
        return await detailed_http_exception_handler(request, HttpTicketUpdateError())
    if isinstance(exc, TicketDeletionError):
        return await detailed_http_exception_handler(request, TicketDeleteError())

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


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        msg = first_error.get("msg", "Invalid request")
        
        # Clean Pydantic prefix
        clean_msg = msg
        if msg.startswith("Value error, "):
            clean_msg = msg.replace("Value error, ", "")
            
        # Only return 400 if it matches known password errors
        if clean_msg == ErrorCode.PASSWORD_MISMATCH or clean_msg == ErrorCode.PASSWORD_RULES:
            return JSONResponse(status_code=400, content={"detail": clean_msg})

    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())},
    )
