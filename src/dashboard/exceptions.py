from src.dashboard.constants import DomainErrorCode
from src.exceptions import DomainException


class StatsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.STATS_FETCH_FAILED
