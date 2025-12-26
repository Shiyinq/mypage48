from src.api_keys.constants import DomainErrorCode
from src.exceptions import DomainException


class APIKeyCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.API_KEY_CREATION_FAILED


class APIKeyDeletionError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.API_KEY_DELETION_FAILED


class APIKeyNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.API_KEY_NOT_FOUND


class InvalidAPIKeyError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_API_KEY
