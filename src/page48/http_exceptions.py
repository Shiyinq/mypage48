from src.http_exceptions import (
    BadRequest,
    EntityTooLarge,
    InternalServerError,
    NotFound,
    PermissionDenied,
)
from src.page48.constants import ErrorCode


class PostNotFound(NotFound):
    DETAIL = ErrorCode.POST_NOT_FOUND


class PostCreateError(InternalServerError):
    DETAIL = ErrorCode.POST_CREATE_ERROR


class UnauthorizedAction(PermissionDenied):
    DETAIL = ErrorCode.UNAUTHORIZED_ACTION


class MaxMediaExceeded(BadRequest):
    DETAIL = ErrorCode.MAX_MEDIA_EXCEEDED


class ReplyNotFound(NotFound):
    DETAIL = ErrorCode.REPLY_NOT_FOUND


class UserProfileNotFound(NotFound):
    DETAIL = ErrorCode.USER_NOT_FOUND


class ReportCreateError(InternalServerError):
    DETAIL = ErrorCode.REPORT_CREATE_ERROR


class CannotReportSelf(BadRequest):
    DETAIL = ErrorCode.CANNOT_REPORT_SELF


class ReportAlreadyExists(BadRequest):
    DETAIL = ErrorCode.REPORT_ALREADY_EXISTS


class InvalidReportTarget(BadRequest):
    DETAIL = ErrorCode.INVALID_REPORT_TARGET


class VideoUploadError(InternalServerError):
    DETAIL = ErrorCode.VIDEO_UPLOAD_ERROR


class VideoTooLarge(EntityTooLarge):
    DETAIL = ErrorCode.VIDEO_TOO_LARGE


class InvalidVideoType(BadRequest):
    DETAIL = ErrorCode.INVALID_VIDEO_TYPE


class MaxVideoExceeded(BadRequest):
    DETAIL = ErrorCode.MAX_VIDEO_EXCEEDED


class MediaConflict(BadRequest):
    DETAIL = ErrorCode.INVALID_MEDIA_COMBINATION


class InvalidVideo(BadRequest):
    DETAIL = ErrorCode.INVALID_VIDEO
