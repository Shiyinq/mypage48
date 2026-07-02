from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.achievements.exceptions import AchievementsFetchError
from src.achievements.http_exceptions import AchievementsFetchHTTPException
from src.admin.exceptions import AdminStatsFetchError
from src.admin.http_exceptions import HttpAdminStatsFetchError
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
from src.dashboard.exceptions import StatsFetchError
from src.dashboard.http_exceptions import StatsFetchFailed
from src.events.exceptions import (
    EventCreationError,
    EventFetchError,
    EventNotFoundError,
)
from src.events.http_exceptions import EventCreateError, EventFetchFailed, EventNotFound
from src.exceptions import DomainException, InvalidDateError
from src.export.exceptions import ExportInProgressError, ExportNotFoundError
from src.export.http_exceptions import ExportInProgress, ExportNotFound
from src.feedback.exceptions import (
    FeedbackCreationError,
    FeedbackDeleteError,
    FeedbackFetchError,
    FeedbackNotFound,
    FeedbackUpdateError,
)
from src.feedback.http_exceptions import (
    FeedbackCreateError,
    FeedbackDeleteFailed,
    FeedbackFetchFailed,
)
from src.feedback.http_exceptions import FeedbackNotFound as HttpFeedbackNotFound
from src.feedback.http_exceptions import FeedbackUpdateFailed
from src.http_exceptions import DetailedHTTPException
from src.live.exceptions import (
    CommentsFetchError,
    FetchIdnError,
    FetchShowroomError,
    ProxyError,
    StreamingUrlNotFoundError,
)
from src.live.http_exceptions import (
    CommentsFetchFailed,
    IdnFetchFailed,
    ProxyRequestFailed,
    ShowroomFetchFailed,
    StreamingUrlNotFound,
)
from src.live_history.exceptions import LiveHistoryNotFoundError, LiveHistoryUpdateError
from src.live_history.http_exceptions import (
    LiveHistoryInvalidDate,
    LiveHistoryNotFound,
    LiveHistoryUpdateFailed,
)
from src.llm.exceptions import ImageAnalysisError
from src.llm.exceptions import ImageTooLargeError as LLMImageTooLargeError
from src.llm.exceptions import InvalidImageError as LLMInvalidImageError
from src.llm.exceptions import InvalidImageTypeError as LLMInvalidImageTypeError
from src.llm.http_exceptions import ImageAnalysisFailed
from src.llm.http_exceptions import ImageTooLarge as LLMImageTooLarge
from src.llm.http_exceptions import InvalidImage as LLMInvalidImage
from src.llm.http_exceptions import InvalidImageType as LLMInvalidImageType
from src.logging_config import create_logger
from src.members.exceptions import MemberFetchError, MemberNotFoundError
from src.members.http_exceptions import MemberFetchError as MemberFetchHTTPException
from src.members.http_exceptions import MemberNotFound
from src.memories.exceptions import MemoriesFetchError
from src.memories.http_exceptions import MemoriesFetchHTTPException
from src.news.exceptions import NewsFetchError, NewsItemFetchError, NewsNotFoundError
from src.news.http_exceptions import (
    NewsFetchHTTPError,
    NewsItemFetchHTTPError,
    NewsNotFound,
)
from src.replay.exceptions import ReplayAlreadyExists, ReplayNotFound, ReplayUploadError
from src.replay.http_exceptions import (
    HttpReplayAlreadyExists,
    HttpReplayNotFound,
    HttpReplayUploadError,
)
from src.setlists.exceptions import SetlistFetchError, SetlistNotFoundError
from src.setlists.http_exceptions import SetlistFetchError as SetlistFetchHTTPException
from src.setlists.http_exceptions import SetlistNotFound
from src.sorter.exceptions import (
    SorterDeleteError,
    SorterNotFoundError,
    SorterSaveError,
)
from src.sorter.http_exceptions import (
    SorterDeleteFailed,
    SorterNotFound,
    SorterSaveFailed,
)
from src.storage.exceptions import ImageNotFoundError as StorageImageNotFoundError
from src.storage.exceptions import ImageUploadError as StorageImageUploadError
from src.storage.exceptions import (
    InvalidCategoryError,
    PresignedUrlError,
    StorageConnectionError,
)
from src.storage.http_exceptions import ImageNotFound as StorageImageNotFound
from src.storage.http_exceptions import ImageUploadFailed as StorageImageUploadFailed
from src.storage.http_exceptions import (
    InvalidCategory,
    PresignedUrlFailed,
    StorageConnectionFailed,
)
from src.tickets.exceptions import ImageTooLargeError as TheaterImageTooLargeError
from src.tickets.exceptions import InvalidImageError as TheaterInvalidImageError
from src.tickets.exceptions import InvalidImageTypeError as TheaterInvalidImageTypeError
from src.tickets.exceptions import InvalidPhotoTypeError as TheaterInvalidPhotoTypeError
from src.tickets.exceptions import (
    TicketCreationError,
    TicketDeletionError,
    TicketFetchError,
    TicketNotFoundError,
    TicketUpdateError,
)
from src.tickets.http_exceptions import ImageTooLarge as TheaterImageTooLarge
from src.tickets.http_exceptions import InvalidImage as TheaterInvalidImage
from src.tickets.http_exceptions import InvalidImageType as TheaterInvalidImageType
from src.tickets.http_exceptions import InvalidPhotoType as TheaterInvalidPhotoType
from src.tickets.http_exceptions import TicketCreateError, TicketDeleteError
from src.tickets.http_exceptions import TicketFetchError as HttpTicketFetchError
from src.tickets.http_exceptions import TicketNotFound
from src.tickets.http_exceptions import TicketUpdateError as HttpTicketUpdateError
from src.users.constants import ErrorCode
from src.users.exceptions import AccountLocked as DomainAccountLocked
from src.users.exceptions import EmailAlreadyExistsError
from src.users.exceptions import EmailNotVerified as DomainEmailNotVerified
from src.users.exceptions import ImageTooLargeError as UserImageTooLargeError
from src.users.exceptions import InvalidImageError as UserInvalidImageError
from src.users.exceptions import InvalidImageTypeError as UserInvalidImageTypeError
from src.users.exceptions import (
    OshiAlreadyExistsError,
    OshiLimitReachedError,
    OshiNotFoundError,
    OshiUpdateError,
    ProfileStatsFetchError,
    ProviderUserCreationError,
    PublicStatusUpdateError,
    PublicUserNotFoundError,
    UserCreationError,
    UserFetchError,
    UsernameAlreadyExistsError,
    UserUpdateError,
)
from src.users.http_exceptions import EmailTaken
from src.users.http_exceptions import ImageTooLarge as UserImageTooLarge
from src.users.http_exceptions import InvalidImage as UserInvalidImage
from src.users.http_exceptions import InvalidImageType as UserInvalidImageType
from src.users.http_exceptions import (
    OshiAlreadyExists,
    OshiLimitReached,
    OshiNotFound,
    OshiUpdateFailed,
    ProfileStatsFetchFailed,
    PublicStatusUpdateFailed,
    PublicUserNotFound,
    ServerError,
    UserFetchFailed,
    UsernameTaken,
    UserUpdateFailed,
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
    if isinstance(exc, OshiLimitReachedError):
        return await detailed_http_exception_handler(request, OshiLimitReached())
    if isinstance(exc, OshiAlreadyExistsError):
        return await detailed_http_exception_handler(request, OshiAlreadyExists())
    if isinstance(exc, OshiNotFoundError):
        return await detailed_http_exception_handler(request, OshiNotFound())
    if isinstance(exc, PublicStatusUpdateError):
        return await detailed_http_exception_handler(
            request, PublicStatusUpdateFailed()
        )
    if isinstance(exc, ProfileStatsFetchError):
        return await detailed_http_exception_handler(request, ProfileStatsFetchFailed())

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
    if isinstance(exc, TheaterInvalidPhotoTypeError):
        return await detailed_http_exception_handler(request, TheaterInvalidPhotoType())

    # Admin errors
    if isinstance(exc, AdminStatsFetchError):
        return await detailed_http_exception_handler(
            request, HttpAdminStatsFetchError()
        )

    # LLM errors
    if isinstance(exc, ImageAnalysisError):
        return await detailed_http_exception_handler(request, ImageAnalysisFailed())
    if isinstance(exc, LLMImageTooLargeError):
        return await detailed_http_exception_handler(request, LLMImageTooLarge())
    if isinstance(exc, LLMInvalidImageTypeError):
        return await detailed_http_exception_handler(request, LLMInvalidImageType())
    if isinstance(exc, LLMInvalidImageError):
        return await detailed_http_exception_handler(request, LLMInvalidImage())

    # Dashboard errors
    if isinstance(exc, StatsFetchError):
        return await detailed_http_exception_handler(request, StatsFetchFailed())

    # Achievements errors
    if isinstance(exc, AchievementsFetchError):
        return await detailed_http_exception_handler(
            request, AchievementsFetchHTTPException()
        )

    # Memories errors
    if isinstance(exc, MemoriesFetchError):
        return await detailed_http_exception_handler(
            request, MemoriesFetchHTTPException()
        )

    # Setlists errors
    if isinstance(exc, SetlistNotFoundError):
        return await detailed_http_exception_handler(request, SetlistNotFound())
    if isinstance(exc, SetlistFetchError):
        return await detailed_http_exception_handler(
            request, SetlistFetchHTTPException()
        )

    # Members errors
    if isinstance(exc, MemberNotFoundError):
        return await detailed_http_exception_handler(request, MemberNotFound())
    if isinstance(exc, MemberFetchError):
        return await detailed_http_exception_handler(
            request, MemberFetchHTTPException()
        )

    # Events errors
    if isinstance(exc, EventNotFoundError):
        return await detailed_http_exception_handler(request, EventNotFound())
    if isinstance(exc, EventCreationError):
        return await detailed_http_exception_handler(request, EventCreateError())
    if isinstance(exc, EventFetchError):
        return await detailed_http_exception_handler(request, EventFetchFailed())

    # Feedback errors
    if isinstance(exc, FeedbackCreationError):
        return await detailed_http_exception_handler(request, FeedbackCreateError())
    if isinstance(exc, FeedbackFetchError):
        return await detailed_http_exception_handler(request, FeedbackFetchFailed())
    if isinstance(exc, FeedbackNotFound):
        return await detailed_http_exception_handler(request, HttpFeedbackNotFound())
    if isinstance(exc, FeedbackUpdateError):
        return await detailed_http_exception_handler(request, FeedbackUpdateFailed())
    if isinstance(exc, FeedbackDeleteError):
        return await detailed_http_exception_handler(request, FeedbackDeleteFailed())

    # News errors
    if isinstance(exc, NewsNotFoundError):
        return await detailed_http_exception_handler(request, NewsNotFound())
    if isinstance(exc, NewsFetchError):
        return await detailed_http_exception_handler(request, NewsFetchHTTPError())
    if isinstance(exc, NewsItemFetchError):
        return await detailed_http_exception_handler(request, NewsItemFetchHTTPError())

    # Sorter exceptions
    if isinstance(exc, SorterNotFoundError):
        return await detailed_http_exception_handler(request, SorterNotFound())
    if isinstance(exc, SorterSaveError):
        return await detailed_http_exception_handler(request, SorterSaveFailed())
    if isinstance(exc, SorterDeleteError):
        return await detailed_http_exception_handler(request, SorterDeleteFailed())

    # Live exceptions
    if isinstance(exc, FetchShowroomError):
        return await detailed_http_exception_handler(request, ShowroomFetchFailed())
    if isinstance(exc, FetchIdnError):
        return await detailed_http_exception_handler(request, IdnFetchFailed())
    if isinstance(exc, StreamingUrlNotFoundError):
        return await detailed_http_exception_handler(request, StreamingUrlNotFound())
    if isinstance(exc, ProxyError):
        return await detailed_http_exception_handler(request, ProxyRequestFailed())
    if isinstance(exc, CommentsFetchError):
        return await detailed_http_exception_handler(request, CommentsFetchFailed())

    # Live History exceptions
    if isinstance(exc, LiveHistoryNotFoundError):
        return await detailed_http_exception_handler(request, LiveHistoryNotFound())
    if isinstance(exc, LiveHistoryUpdateError):
        return await detailed_http_exception_handler(request, LiveHistoryUpdateFailed())
    if isinstance(exc, InvalidDateError):
        return await detailed_http_exception_handler(request, LiveHistoryInvalidDate())

    # Export errors
    if isinstance(exc, ExportInProgressError):
        return await detailed_http_exception_handler(request, ExportInProgress())
    if isinstance(exc, ExportNotFoundError):
        return await detailed_http_exception_handler(request, ExportNotFound())

    # Replay errors
    if isinstance(exc, ReplayAlreadyExists):
        return await detailed_http_exception_handler(request, HttpReplayAlreadyExists())
    if isinstance(exc, ReplayUploadError):
        return await detailed_http_exception_handler(request, HttpReplayUploadError())
    if isinstance(exc, ReplayNotFound):
        return await detailed_http_exception_handler(request, HttpReplayNotFound())

    # Storage errors
    if isinstance(exc, StorageConnectionError):
        return await detailed_http_exception_handler(request, StorageConnectionFailed())
    if isinstance(exc, StorageImageUploadError):
        return await detailed_http_exception_handler(
            request, StorageImageUploadFailed()
        )
    if isinstance(exc, StorageImageNotFoundError):
        return await detailed_http_exception_handler(request, StorageImageNotFound())
    if isinstance(exc, PresignedUrlError):
        return await detailed_http_exception_handler(request, PresignedUrlFailed())
    if isinstance(exc, InvalidCategoryError):
        return await detailed_http_exception_handler(request, InvalidCategory())

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
        if (
            clean_msg == ErrorCode.PASSWORD_MISMATCH
            or clean_msg == ErrorCode.PASSWORD_RULES
        ):
            return JSONResponse(status_code=400, content={"detail": clean_msg})

    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())},
    )
