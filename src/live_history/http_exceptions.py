from fastapi import status
from src.http_exceptions import DetailedHTTPException

class LiveHistoryNotFound(DetailedHTTPException):
    STATUS_CODE = status.HTTP_404_NOT_FOUND
    DETAIL = "Live history not found"

class LiveHistoryUpdateFailed(DetailedHTTPException):
    STATUS_CODE = status.HTTP_500_INTERNAL_SERVER_ERROR
    DETAIL = "Failed to update live history"
