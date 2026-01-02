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
    AuthOperationError,
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
    AuthOperationFailed,
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
    ImageTooLargeError as UserImageTooLargeError,
    InvalidImageError as UserInvalidImageError,
    InvalidImageTypeError as UserInvalidImageTypeError,
    OshiUpdateError,
    ProviderUserCreationError,
    PublicStatusUpdateError,
    PublicUserNotFoundError,
    UserCreationError,
    UserFetchError,
    UserUpdateError,
    UsernameAlreadyExistsError,
)
from src.users.http_exceptions import (
    EmailTaken,
    ImageTooLarge as UserImageTooLarge,
    InvalidImage as UserInvalidImage,
    InvalidImageType as UserInvalidImageType,
    OshiUpdateFailed,
    PublicStatusUpdateFailed,
    PublicUserNotFound,
    ServerError,
    UserFetchFailed,
    UserUpdateFailed,
    UsernameTaken,
)
from src.users.constants import ErrorCode
from src.theater.exceptions import (
    ImageTooLargeError as TheaterImageTooLargeError,
    InvalidImageError as TheaterInvalidImageError,
    InvalidImageTypeError as TheaterInvalidImageTypeError,
    TicketNotFoundError,
    TicketCreationError,
    TicketFetchError,
    TicketUpdateError,
    TicketDeletionError,
)
from src.theater.http_exceptions import (
    ImageTooLarge as TheaterImageTooLarge,
    InvalidImage as TheaterInvalidImage,
    InvalidImageType as TheaterInvalidImageType,
    TicketNotFound,
    TicketCreateError,
    TicketFetchError as HttpTicketFetchError,
    TicketUpdateError as HttpTicketUpdateError,
    TicketDeleteError,
)
from src.llm.exceptions import (
    ImageAnalysisError,
    ImageTooLargeError as LLMImageTooLargeError,
    InvalidImageError as LLMInvalidImageError,
    InvalidImageTypeError as LLMInvalidImageTypeError,
)
from src.llm.http_exceptions import (
    ImageAnalysisFailed,
    ImageTooLarge as LLMImageTooLarge,
    InvalidImage as LLMInvalidImage,
    InvalidImageType as LLMInvalidImageType,
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
    if isinstance(exc, AuthOperationError):
        return await detailed_http_exception_handler(request, AuthOperationFailed())

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

    # Users update/fetch errors
    if isinstance(exc, UserUpdateError):
        return await detailed_http_exception_handler(request, UserUpdateFailed())
    if isinstance(exc, UserFetchError):
        return await detailed_http_exception_handler(request, UserFetchFailed())
    if isinstance(exc, OshiUpdateError):
        return await detailed_http_exception_handler(request, OshiUpdateFailed())
    if isinstance(exc, PublicStatusUpdateError):
        return await detailed_http_exception_handler(request, PublicStatusUpdateFailed())

    # Users image validation errors
    if isinstance(exc, UserImageTooLargeError):
        return await detailed_http_exception_handler(request, UserImageTooLarge())
    if isinstance(exc, UserInvalidImageTypeError):
        return await detailed_http_exception_handler(request, UserInvalidImageType())
    if isinstance(exc, UserInvalidImageError):
        return await detailed_http_exception_handler(request, UserInvalidImage())

    # Theater ticket errors
    if isinstance(exc, TicketNotFoundError):
        return await detailed_http_exception_handler(request, TicketNotFound())
    if isinstance(exc, TicketCreationError):
        return await detailed_http_exception_handler(request, TicketCreateError())
    if isinstance(exc, TicketFetchError):
        return await detailed_http_exception_handler(request, HttpTicketFetchError())
    if isinstance(exc, TicketUpdateError):
        return await detailed_http_exception_handler(request, HttpTicketUpdateError())
    if isinstance(exc, TicketDeletionError):
        return await detailed_http_exception_handler(request, TicketDeleteError())

    # Theater image validation errors
    if isinstance(exc, TheaterImageTooLargeError):
        return await detailed_http_exception_handler(request, TheaterImageTooLarge())
    if isinstance(exc, TheaterInvalidImageTypeError):
        return await detailed_http_exception_handler(request, TheaterInvalidImageType())
    if isinstance(exc, TheaterInvalidImageError):
        return await detailed_http_exception_handler(request, TheaterInvalidImage())

    # LLM errors
    if isinstance(exc, ImageAnalysisError):
        return await detailed_http_exception_handler(request, ImageAnalysisFailed())
    if isinstance(exc, LLMImageTooLargeError):
        return await detailed_http_exception_handler(request, LLMImageTooLarge())
    if isinstance(exc, LLMInvalidImageTypeError):
        return await detailed_http_exception_handler(request, LLMInvalidImageType())
    if isinstance(exc, LLMInvalidImageError):
        return await detailed_http_exception_handler(request, LLMInvalidImage())

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
