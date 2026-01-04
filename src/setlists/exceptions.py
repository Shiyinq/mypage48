from src.exceptions import DomainException
from src.setlists.constants import DomainErrorCode


class SetlistNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SETLIST_NOT_FOUND


class SetlistFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SETLIST_FETCH_FAILED
