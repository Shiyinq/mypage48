from src.exceptions import DomainException
from src.llm.constants import DomainErrorCode


class ImageAnalysisError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.ANALYSIS_FAILED


class ImageTooLargeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.IMAGE_TOO_LARGE


class InvalidImageTypeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_IMAGE_TYPE


class InvalidImageError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_IMAGE
