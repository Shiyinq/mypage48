from src.exceptions import DomainException
from src.dashboard.constants import DomainErrorCode


class StatsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.STATS_FETCH_FAILED
