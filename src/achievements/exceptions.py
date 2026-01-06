from src.achievements.constants import DomainErrorCode
from src.exceptions import DomainException


class AchievementsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.FETCH_FAILED
