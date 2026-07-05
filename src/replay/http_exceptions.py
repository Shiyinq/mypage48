from src.http_exceptions import Conflict, InternalServerError, NotFound
from src.replay.constants import ErrorCode


class HttpReplayUploadError(InternalServerError):
    DETAIL = ErrorCode.REPLAY_UPLOAD_FAILED


class HttpReplayNotFound(NotFound):
    DETAIL = ErrorCode.REPLAY_NOT_FOUND


class HttpReplayAlreadyExists(Conflict):
    DETAIL = ErrorCode.REPLAY_ALREADY_EXISTS
