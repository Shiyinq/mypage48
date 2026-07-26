from src.concerts.constants import DomainErrorCode
from src.exceptions import DomainException


class ConcertCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.CONCERT_CREATION_FAILED


class ConcertUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.CONCERT_UPDATE_FAILED


class ConcertDeleteError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.CONCERT_DELETE_FAILED


class ConcertNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.CONCERT_NOT_FOUND
