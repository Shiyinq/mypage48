from src.admin.constants import DomainErrorCode
from src.exceptions import DomainException


class AdminStatsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.ADMIN_STATS_FETCH_FAILED
