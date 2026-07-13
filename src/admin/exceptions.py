from src.admin.constants import DomainErrorCode
from src.exceptions import DomainException


class AdminStatsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.ADMIN_STATS_FETCH_FAILED


class AdminConfigFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.ADMIN_CONFIG_FETCH_FAILED


class AdminConfigUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.ADMIN_CONFIG_UPDATE_FAILED
