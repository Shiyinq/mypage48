from src.exceptions import DomainException
from src.feedback.constants import DomainErrorCode


class FeedbackCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.FEEDBACK_CREATION_FAILED


class FeedbackFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.FEEDBACK_FETCH_FAILED


class FeedbackNotFound(DomainException):
    ERROR_MESSAGE = DomainErrorCode.FEEDBACK_NOT_FOUND
