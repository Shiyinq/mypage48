from src.members.constants import ErrorCode
from src.http_exceptions import InternalServerError, NotFound


class MemberNotFound(NotFound):
    DETAIL = ErrorCode.MEMBER_NOT_FOUND


class MemberFetchError(InternalServerError):
    DETAIL = ErrorCode.MEMBER_FETCH_ERROR
