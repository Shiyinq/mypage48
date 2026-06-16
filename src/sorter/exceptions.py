from src.exceptions import DomainException
from src.sorter.constants import DomainErrorCode


class SorterNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SORTER_NOT_FOUND


class SorterSaveError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SORTER_CREATION_FAILED


class SorterDeleteError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SORTER_DELETION_FAILED
