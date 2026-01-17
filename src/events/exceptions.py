from src.events.constants import DomainErrorCode
from src.exceptions import DomainException


class EventCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.EVENT_CREATION_FAILED


class EventNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.EVENT_NOT_FOUND


class EventFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.EVENT_FETCH_FAILED
