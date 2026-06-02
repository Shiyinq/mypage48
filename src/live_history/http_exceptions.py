from src.http_exceptions import InternalServerError, NotFound
from src.live_history.constants import ErrorCode


class LiveHistoryNotFound(NotFound):
    DETAIL = ErrorCode.LIVE_HISTORY_NOT_FOUND


class LiveHistoryUpdateFailed(InternalServerError):
    DETAIL = ErrorCode.LIVE_HISTORY_UPDATE_FAILED
