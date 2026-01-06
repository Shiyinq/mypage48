from src.http_exceptions import BadRequest, InternalServerError
from src.llm.constants import ErrorCode


class ImageAnalysisFailed(InternalServerError):
    DETAIL = ErrorCode.ANALYSIS_FAILED


class ImageTooLarge(BadRequest):
    DETAIL = ErrorCode.IMAGE_TOO_LARGE


class InvalidImageType(BadRequest):
    DETAIL = ErrorCode.INVALID_IMAGE_TYPE


class InvalidImage(BadRequest):
    DETAIL = ErrorCode.INVALID_IMAGE
