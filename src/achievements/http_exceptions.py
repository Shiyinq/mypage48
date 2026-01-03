from src.http_exceptions import InternalServerError
from src.achievements.constants import ErrorCode


class AchievementsFetchHTTPException(InternalServerError):
    DETAIL = ErrorCode.FETCH_FAILED
