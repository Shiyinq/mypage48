from src.http_exceptions import BadRequest, Forbidden, InternalServerError, NotFound
from src.page48.constants import ErrorCode


class PostNotFound(NotFound):
    DETAIL = ErrorCode.POST_NOT_FOUND


class PostCreateError(InternalServerError):
    DETAIL = ErrorCode.POST_CREATE_ERROR


class UnauthorizedAction(Forbidden):
    DETAIL = ErrorCode.UNAUTHORIZED_ACTION


class MaxMediaExceeded(BadRequest):
    DETAIL = ErrorCode.MAX_MEDIA_EXCEEDED


class ReplyNotFound(NotFound):
    DETAIL = ErrorCode.REPLY_NOT_FOUND


class UserProfileNotFound(NotFound):
    DETAIL = ErrorCode.USER_NOT_FOUND
