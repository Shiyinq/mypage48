from src.exceptions import DomainException
from src.llm.constants import DomainErrorCode


class ImageAnalysisError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.ANALYSIS_FAILED
