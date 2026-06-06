from src.exceptions import DomainException
from src.live_history.constants import DomainErrorCode


class LiveHistoryNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.LIVE_HISTORY_NOT_FOUND_ERROR


class LiveHistoryUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.LIVE_HISTORY_UPDATE_ERROR
