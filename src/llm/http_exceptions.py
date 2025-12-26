from src.http_exceptions import InternalServerError
from src.llm.constants import ErrorCode


class ImageAnalysisFailed(InternalServerError):
    DETAIL = ErrorCode.ANALYSIS_FAILED
