from src.setlists.constants import DomainErrorCode
from src.exceptions import DomainException


class SetlistNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SETLIST_NOT_FOUND


class SetlistFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SETLIST_FETCH_FAILED
