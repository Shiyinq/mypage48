from enum import Enum


class ErrorCode:
    FEEDBACK_CREATE_ERROR = "Failed to submit feedback"
    FEEDBACK_FETCH_ERROR = "Failed to fetch feedback list"
    FEEDBACK_NOT_FOUND = "Feedback not found"


class DomainErrorCode:
    FEEDBACK_CREATION_FAILED = "Failed to create feedback"
    FEEDBACK_FETCH_FAILED = "Failed to fetch feedback"
    FEEDBACK_NOT_FOUND = "Feedback not found"


class FeedbackType(str, Enum):
    ISSUE = "issue"
    SUGGESTION = "suggestion"
    OTHER = "other"
