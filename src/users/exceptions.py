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


class PublicUserNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PUBLIC_USER_NOT_FOUND


class ImageTooLargeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.IMAGE_TOO_LARGE


class InvalidImageTypeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_IMAGE_TYPE


class InvalidImageError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_IMAGE


class UserUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.USER_UPDATE_FAILED


class UserFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.USER_FETCH_FAILED


class OshiUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.OSHI_UPDATE_FAILED


class PublicStatusUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PUBLIC_STATUS_UPDATE_FAILED


class ProfileStatsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PROFILE_STATS_FETCH_FAILED


class OshiLimitReachedError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.OSHI_LIMIT_REACHED


class OshiAlreadyExistsError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.OSHI_ALREADY_EXISTS


class OshiNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.OSHI_NOT_FOUND
