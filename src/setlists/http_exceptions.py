from src.http_exceptions import InternalServerError, NotFound
from src.setlists.constants import ErrorCode


class SetlistNotFound(NotFound):
    DETAIL = ErrorCode.SETLIST_NOT_FOUND


class SetlistFetchError(InternalServerError):
    DETAIL = ErrorCode.SETLIST_FETCH_ERROR
