from src.export.constants import ErrorCode
from src.http_exceptions import Conflict, NotFound


class ExportInProgress(Conflict):
    DETAIL = ErrorCode.EXPORT_IN_PROGRESS


class ExportNotFound(NotFound):
    DETAIL = ErrorCode.EXPORT_NOT_FOUND
