from src.auth.constants import ErrorCode
from src.http_exceptions import BadRequest, NotAuthenticated, NotFound, PermissionDenied


class IncorrectEmailOrPassword(NotAuthenticated):
    DETAIL = ErrorCode.INCORRECT_EMAIL_OR_PASSWORD


class InvalidRefreshToken(NotAuthenticated):
    DETAIL = ErrorCode.INVALID_REFRESH_TOKEN


class InvalidJWTToken(NotAuthenticated):
    DETAIL = ErrorCode.INVALID_JWT_TOKEN


class RefreshTokenExpired(NotAuthenticated):
    DETAIL = ErrorCode.REFRESH_TOKEN_EXPIRED


class SuspiciousActivity(NotAuthenticated):
    DETAIL = ErrorCode.SUSPICIOUS_ACTIVITY


class AccountLocked(BadRequest):  # Assuming 400 for now, or use Forbidden (403)
    DETAIL = ErrorCode.ACCOUNT_LOCKED


class EmailNotVerified(BadRequest):
    DETAIL = ErrorCode.EMAIL_NOT_VERIFIED


class InvalidCSRFToken(PermissionDenied):
    DETAIL = ErrorCode.INVALID_CSRF_TOKEN


class EmailNotFoundOrVerified(NotFound):
    DETAIL = ErrorCode.EMAIL_NOT_FOUND_OR_VERIFIED


class VerificationTokenInvalid(BadRequest):
    DETAIL = ErrorCode.VERIFICATION_TOKEN_INVALID


class PasswordResetTokenInvalid(BadRequest):
    DETAIL = ErrorCode.PASSWORD_RESET_TOKEN_INVALID


class PasswordsNotMatch(BadRequest):
    DETAIL = ErrorCode.PASSWORDS_NOT_MATCH


class PasswordPolicyViolation(BadRequest):
    DETAIL = ErrorCode.PASSWORD_POLICY_VIOLATION
