from src.replay.constants import DomainErrorCode
from src.exceptions import DomainException


class ReplayUploadError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.REPLAY_UPLOAD_FAILED


class ReplayNotFound(DomainException):
    ERROR_MESSAGE = DomainErrorCode.REPLAY_NOT_FOUND
