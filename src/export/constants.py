from enum import Enum


class ExportStatus(str, Enum):
    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ErrorCode:
    EXPORT_IN_PROGRESS = "Export already in progress."
    EXPORT_NOT_FOUND = "Export file not available or expired."
    EXPORT_EXPIRED = "Export file expired."


class DomainErrorCode:
    EXPORT_IN_PROGRESS = "Export already in progress."
    EXPORT_NOT_FOUND = "Export file not available or expired."
    EXPORT_EXPIRED = "Export file expired."
