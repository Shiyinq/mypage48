from src.exceptions import DomainException
from src.export.constants import DomainErrorCode


class ExportInProgressError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.EXPORT_IN_PROGRESS


class ExportNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.EXPORT_NOT_FOUND
