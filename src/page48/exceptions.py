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
