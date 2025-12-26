class ErrorCode:
    USERNAME_TAKEN = "Username already exist."
    EMAIL_TAKEN = "Email already exist."
    PASSWORD_MISMATCH = "The two passwords did not match."
    PASSWORD_RULES = "Password must contain at least 8 characters, including uppercase, lowercase, digits, and symbols. No spaces allowed."


class DomainErrorCode:
    USER_CREATION_FAILED = "Failed to create user"
    USERNAME_ALREADY_EXISTS = "Username already exists"
    EMAIL_ALREADY_EXISTS = "Email already exists"
    PROVIDER_USER_CREATION_FAILED = "Failed to create provider user"
    EMAIL_VERIFICATION_FAILED = "Email verification failed"
    USER_NOT_FOUND = "User not found"
    INVALID_USER_DATA = "Invalid user data"
    ACCOUNT_LOCKED = "Account is locked"
    EMAIL_NOT_VERIFIED = "Email not verified"


class Info:
    USER_CREATED = "Register success."
    USER_CREATED_WITH_EMAIL = (
        "Register success. Please check your email for verification link."
    )
