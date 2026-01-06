from src.dashboard.constants import ErrorCode
from src.http_exceptions import InternalServerError


class StatsFetchFailed(InternalServerError):
    DETAIL = ErrorCode.STATS_FETCH_ERROR
