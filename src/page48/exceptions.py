from src.exceptions import DomainException
from src.page48.constants import DomainErrorCode


class PostCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POST_CREATION_FAILED


class PostNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.POST_NOT_FOUND


class UnauthorizedActionError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.UNAUTHORIZED


class UserProfileNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.USER_NOT_FOUND


class ReportCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.REPORT_CREATION_FAILED


class CannotReportSelfError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.CANNOT_REPORT_SELF


class ReportAlreadyExistsError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.REPORT_ALREADY_EXISTS


class InvalidReportTargetError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_REPORT_TARGET
