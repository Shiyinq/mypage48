from src.exceptions import DomainException
from src.live.constants import DomainErrorCode


class FetchShowroomError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.FETCH_SHOWROOM_ERROR


class FetchIdnError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.FETCH_IDN_ERROR


class StreamingUrlNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.STREAMING_URL_NOT_FOUND


class ProxyError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PROXY_ERROR


class CommentsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.COMMENTS_FETCH_ERROR


class GiftsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.GIFTS_FETCH_ERROR
