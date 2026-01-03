from src.http_exceptions import InternalServerError
from src.memories.constants import ErrorCode


class MemoriesFetchHTTPException(InternalServerError):
    DETAIL = ErrorCode.FETCH_FAILED
