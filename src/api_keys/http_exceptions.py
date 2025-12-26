from src.api_keys.constants import ErrorCode
from src.http_exceptions import BadRequest, InternalServerError, NotFound


class APIKeyNotFound(NotFound):
    DETAIL = ErrorCode.API_KEY_NOT_FOUND


class APIKeyCreateError(InternalServerError):
    DETAIL = ErrorCode.API_KEY_CREATE_ERROR


class APIKeyDeleteError(InternalServerError):
    DETAIL = ErrorCode.API_KEY_DELETE_ERROR


class InvalidAPIKey(BadRequest):
    DETAIL = ErrorCode.INVALID_API_KEY
