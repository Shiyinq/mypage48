from src.http_exceptions import InternalServerError, NotFound
from src.sorter.constants import ErrorCode


class SorterNotFound(NotFound):
    DETAIL = ErrorCode.SORTER_NOT_FOUND


class SorterSaveFailed(InternalServerError):
    DETAIL = ErrorCode.SORTER_SAVE_FAILED


class SorterDeleteFailed(InternalServerError):
    DETAIL = ErrorCode.SORTER_DELETE_FAILED
