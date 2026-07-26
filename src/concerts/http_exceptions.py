from src.concerts.constants import ErrorCode
from src.http_exceptions import InternalServerError, NotFound


class ConcertNotFound(NotFound):
    DETAIL = ErrorCode.CONCERT_NOT_FOUND


class ConcertCreateError(InternalServerError):
    DETAIL = ErrorCode.CONCERT_CREATE_ERROR


class ConcertUpdateError(InternalServerError):
    DETAIL = ErrorCode.CONCERT_UPDATE_ERROR


class ConcertDeleteError(InternalServerError):
    DETAIL = ErrorCode.CONCERT_DELETE_ERROR
