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


class PollNotFound(NotFound):
    DETAIL = ErrorCode.POLL_NOT_FOUND


class PollEnded(BadRequest):
    DETAIL = ErrorCode.POLL_ENDED


class PollAlreadyVoted(BadRequest):
    DETAIL = ErrorCode.POLL_ALREADY_VOTED


class InvalidPollOption(BadRequest):
    DETAIL = ErrorCode.INVALID_POLL_OPTION


class InvalidPollOptions(BadRequest):
    DETAIL = ErrorCode.INVALID_POLL_OPTIONS


class PollMediaConflict(BadRequest):
    DETAIL = ErrorCode.POLL_MEDIA_CONFLICT


class PollReplyNotAllowed(BadRequest):
    DETAIL = ErrorCode.POLL_REPLY_NOT_ALLOWED


class ThreadTooShort(BadRequest):
    DETAIL = ErrorCode.THREAD_TOO_SHORT


class ThreadTooLong(BadRequest):
    DETAIL = ErrorCode.THREAD_TOO_LONG


class QuotedPostNotFound(NotFound):
    DETAIL = ErrorCode.QUOTED_POST_NOT_FOUND


class QuotePollConflict(BadRequest):
    DETAIL = ErrorCode.POLL_QUOTE_CONFLICT


class CannotPinReply(BadRequest):
    DETAIL = ErrorCode.CANNOT_PIN_REPLY


class CannotPrivateReply(BadRequest):
    DETAIL = ErrorCode.CANNOT_PRIVATE_REPLY


class CannotFollowSelf(BadRequest):
    DETAIL = ErrorCode.CANNOT_FOLLOW_SELF


class CannotBlockSelf(BadRequest):
    DETAIL = ErrorCode.CANNOT_BLOCK_SELF


class CannotMuteSelf(BadRequest):
    DETAIL = ErrorCode.CANNOT_MUTE_SELF
