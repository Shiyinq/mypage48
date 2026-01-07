from src.exceptions import DomainException
from src.storage.constants import DomainErrorCode


class StorageConnectionError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.STORAGE_CONNECTION_FAILED


class ImageUploadError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.IMAGE_UPLOAD_FAILED


class ImageNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.IMAGE_NOT_FOUND


class PresignedUrlError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PRESIGNED_URL_FAILED


class InvalidCategoryError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_CATEGORY
