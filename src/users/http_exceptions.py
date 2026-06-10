from src.http_exceptions import BadRequest, Conflict, InternalServerError, NotFound
from src.users.constants import ErrorCode


class UsernameTaken(Conflict):
    DETAIL = ErrorCode.USERNAME_TAKEN


class EmailTaken(Conflict):
    DETAIL = ErrorCode.EMAIL_TAKEN


class PasswordNotMatch(BadRequest):
    DETAIL = ErrorCode.PASSWORD_MISMATCH


class PasswordRules(BadRequest):
    DETAIL = ErrorCode.PASSWORD_RULES


class ServerError(InternalServerError):
    DETAIL = "Internal server error."


class PublicUserNotFound(NotFound):
    DETAIL = ErrorCode.PUBLIC_USER_NOT_FOUND


class ImageTooLarge(BadRequest):
    DETAIL = ErrorCode.IMAGE_TOO_LARGE


class InvalidImageType(BadRequest):
    DETAIL = ErrorCode.INVALID_IMAGE_TYPE


class InvalidImage(BadRequest):
    DETAIL = ErrorCode.INVALID_IMAGE


class UserUpdateFailed(InternalServerError):
    DETAIL = ErrorCode.USER_UPDATE_FAILED


class UserFetchFailed(InternalServerError):
    DETAIL = ErrorCode.USER_FETCH_FAILED


class OshiUpdateFailed(InternalServerError):
    DETAIL = ErrorCode.OSHI_UPDATE_FAILED


class OshiLimitReached(BadRequest):
    DETAIL = ErrorCode.OSHI_LIMIT_REACHED


class OshiAlreadyExists(Conflict):
    DETAIL = ErrorCode.OSHI_ALREADY_EXISTS


class OshiNotFound(NotFound):
    DETAIL = ErrorCode.OSHI_NOT_FOUND


class PublicStatusUpdateFailed(InternalServerError):
    DETAIL = ErrorCode.PUBLIC_STATUS_UPDATE_FAILED


class ProfileStatsFetchFailed(InternalServerError):
    DETAIL = ErrorCode.PROFILE_STATS_FETCH_ERROR
