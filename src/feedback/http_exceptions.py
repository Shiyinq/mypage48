from src.feedback.constants import ErrorCode
from src.http_exceptions import InternalServerError, NotFound


class FeedbackCreateError(InternalServerError):
    DETAIL = ErrorCode.FEEDBACK_CREATE_ERROR


class FeedbackFetchFailed(InternalServerError):
    DETAIL = ErrorCode.FEEDBACK_FETCH_ERROR


class FeedbackNotFound(NotFound):
    DETAIL = ErrorCode.FEEDBACK_NOT_FOUND


class FeedbackUpdateFailed(InternalServerError):
    DETAIL = ErrorCode.FEEDBACK_UPDATE_ERROR


class FeedbackDeleteFailed(InternalServerError):
    DETAIL = ErrorCode.FEEDBACK_DELETE_ERROR
