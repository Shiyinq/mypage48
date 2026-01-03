from src.setlists.constants import ErrorCode
from src.http_exceptions import NotFound, InternalServerError


class SetlistNotFound(NotFound):
    DETAIL = ErrorCode.SETLIST_NOT_FOUND


class SetlistFetchError(InternalServerError):
    DETAIL = ErrorCode.SETLIST_FETCH_ERROR
