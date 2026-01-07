from src.http_exceptions import BadRequest, InternalServerError, NotFound
from src.storage.constants import ErrorCode


class StorageConnectionFailed(InternalServerError):
    DETAIL = ErrorCode.STORAGE_CONNECTION_FAILED


class ImageUploadFailed(InternalServerError):
    DETAIL = ErrorCode.IMAGE_UPLOAD_FAILED


class ImageNotFound(NotFound):
    DETAIL = ErrorCode.IMAGE_NOT_FOUND


class PresignedUrlFailed(InternalServerError):
    DETAIL = ErrorCode.PRESIGNED_URL_FAILED


class InvalidCategory(BadRequest):
    DETAIL = ErrorCode.INVALID_CATEGORY
