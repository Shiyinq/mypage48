from src.exceptions import DomainException
from src.achievements.constants import DomainErrorCode


class AchievementsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.FETCH_FAILED


