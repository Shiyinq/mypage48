from src.admin.constants import ErrorCode
from src.http_exceptions import InternalServerError


class HttpAdminStatsFetchError(InternalServerError):
    DETAIL = ErrorCode.ADMIN_STATS_FETCH_ERROR
