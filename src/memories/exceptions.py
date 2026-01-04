from src.exceptions import DomainException
from src.memories.constants import DomainErrorCode


class MemoriesFetchError(DomainException):
    """Raised when fetching memories fails."""

    ERROR_MESSAGE = DomainErrorCode.FETCH_FAILED
