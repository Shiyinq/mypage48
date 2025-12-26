from src.auth.constants import DomainErrorCode
from src.exceptions import DomainException


class IncorrectCredentialsError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INCORRECT_CREDENTIALS


class InvalidRefreshTokenError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_REFRESH_TOKEN


class RefreshTokenExpiredError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.REFRESH_TOKEN_EXPIRED


class InvalidJWTTokenError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_JWT_TOKEN


class SuspiciousActivityError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.SUSPICIOUS_ACTIVITY_DETECTED


class VerificationTokenInvalidError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.VERIFICATION_TOKEN_INVALID


class PasswordResetTokenInvalidError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PASSWORD_RESET_TOKEN_INVALID


class PasswordsDoNotMatchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PASSWORDS_DO_NOT_MATCH


class PasswordPolicyViolationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.PASSWORD_POLICY_VIOLATION
