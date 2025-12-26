from src.http_exceptions import BadRequest, Conflict, InternalServerError
from src.users.constants import ErrorCode


class UsernameTaken(Conflict):
    DETAIL = ErrorCode.USERNAME_TAKEN


class EmailTaken(Conflict):
    DETAIL = ErrorCode.EMAIL_TAKEN


class PasswordNotMatch(BadRequest):
    DETAIL = ErrorCode.PASSWORD_MISMATCH


class PasswordRules(BadRequest):
    DETAIL = ErrorCode.PASSWORD_RULES


class ServerError(InternalServerError):
    DETAIL = "Internal server error."
