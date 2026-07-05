from src.http_exceptions import InternalServerError, NotFound
from src.live.constants import ErrorCode


class ShowroomFetchFailed(InternalServerError):
    DETAIL = ErrorCode.FETCH_SHOWROOM_FAILED


class IdnFetchFailed(InternalServerError):
    DETAIL = ErrorCode.FETCH_IDN_FAILED


class StreamingUrlNotFound(NotFound):
    DETAIL = ErrorCode.STREAMING_URL_NOT_FOUND


class ProxyRequestFailed(InternalServerError):
    DETAIL = ErrorCode.PROXY_FAILED


class CommentsFetchFailed(InternalServerError):
    DETAIL = ErrorCode.COMMENTS_FETCH_FAILED


class GiftsFetchFailed(InternalServerError):
    DETAIL = ErrorCode.GIFTS_FETCH_FAILED
