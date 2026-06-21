from enum import Enum


class ErrorCode:
    FEEDBACK_CREATE_ERROR = "Failed to submit feedback"
    FEEDBACK_FETCH_ERROR = "Failed to fetch feedback list"
    FEEDBACK_NOT_FOUND = "Feedback not found"
    FEEDBACK_UPDATE_ERROR = "Failed to update feedback"
    FEEDBACK_DELETE_ERROR = "Failed to delete feedback"


class DomainErrorCode:
    FEEDBACK_CREATION_FAILED = "Failed to create feedback"
    FEEDBACK_FETCH_FAILED = "Failed to fetch feedback"
    FEEDBACK_NOT_FOUND = "Feedback not found"
    FEEDBACK_UPDATE_FAILED = "Failed to update feedback"
    FEEDBACK_DELETE_FAILED = "Failed to delete feedback"


class FeedbackType(str, Enum):
    ISSUE = "issue"
    SUGGESTION = "suggestion"
    OTHER = "other"


class FeedbackStatus(str, Enum):
    PENDING = "pending"
    NOTED = "noted"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    SPAM = "spam"
