from src.achievements.constants import ErrorCode
from src.http_exceptions import InternalServerError


class AchievementsFetchHTTPException(InternalServerError):
    DETAIL = ErrorCode.FETCH_FAILED
