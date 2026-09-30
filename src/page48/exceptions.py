from src.exceptions import DomainException
from src.page48.constants import DomainErrorCode


class PostCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POST_CREATION_FAILED


class PostNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POST_NOT_FOUND


class UnauthorizedActionError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.UNAUTHORIZED


class UserProfileNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.USER_NOT_FOUND


class ReportCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.REPORT_CREATION_FAILED


class CannotReportSelfError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.CANNOT_REPORT_SELF


class ReportAlreadyExistsError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.REPORT_ALREADY_EXISTS


class InvalidReportTargetError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_REPORT_TARGET


class VideoUploadError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.VIDEO_UPLOAD_FAILED


class VideoTooLargeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.VIDEO_TOO_LARGE


class InvalidVideoTypeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_VIDEO_TYPE


class MaxVideoExceededError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.MAX_VIDEO_EXCEEDED


class MediaConflictError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_MEDIA_COMBINATION


class InvalidVideoError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_VIDEO


class PollNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POLL_NOT_FOUND


class PollEndedError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POLL_ENDED


class PollAlreadyVotedError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POLL_ALREADY_VOTED


class InvalidPollOptionError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_POLL_OPTION


class InvalidPollOptionsError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_POLL_OPTIONS


class PollMediaConflictError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POLL_MEDIA_CONFLICT


class PollReplyNotAllowedError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POLL_REPLY_NOT_ALLOWED


class ThreadCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.THREAD_CREATION_FAILED


class ThreadTooShortError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.THREAD_TOO_SHORT


class ThreadTooLongError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.THREAD_TOO_LONG


class QuotedPostNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.QUOTED_POST_NOT_FOUND


class QuotePollConflictError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POLL_QUOTE_CONFLICT


class CannotPinReplyError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.CANNOT_PIN_REPLY
