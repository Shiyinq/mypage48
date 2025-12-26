from src.exceptions import DomainException
from src.users.constants import DomainErrorCode


class UserCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.USER_CREATION_FAILED


class UsernameAlreadyExistsError(UserCreationError):
    ERROR_MESSAGE = DomainErrorCode.USERNAME_ALREADY_EXISTS


class EmailAlreadyExistsError(UserCreationError):
    ERROR_MESSAGE = DomainErrorCode.EMAIL_ALREADY_EXISTS


class ProviderUserCreationError(UserCreationError):
    ERROR_MESSAGE = DomainErrorCode.PROVIDER_USER_CREATION_FAILED


class AccountLocked(DomainException):
    ERROR_MESSAGE = DomainErrorCode.ACCOUNT_LOCKED


class EmailNotVerified(DomainException):
    ERROR_MESSAGE = DomainErrorCode.EMAIL_NOT_VERIFIED
