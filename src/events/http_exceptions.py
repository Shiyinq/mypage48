from src.events.constants import ErrorCode
from src.http_exceptions import InternalServerError, NotFound


class EventNotFound(NotFound):
    DETAIL = ErrorCode.EVENT_NOT_FOUND


class EventCreateError(InternalServerError):
    DETAIL = ErrorCode.EVENT_CREATE_ERROR


class EventFetchFailed(InternalServerError):
    DETAIL = ErrorCode.EVENT_FETCH_ERROR
