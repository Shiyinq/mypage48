class ErrorCode:
    USERNAME_TAKEN = "Username already exist."
    EMAIL_TAKEN = "Email already exist."
    PASSWORD_MISMATCH = "The two passwords did not match."
    PASSWORD_RULES = "Password must contain at least 8 characters, including uppercase, lowercase, digits, and symbols. No spaces allowed."
    PUBLIC_USER_NOT_FOUND = "User not found or private."
    IMAGE_TOO_LARGE = "Image is too large. Maximum 3MB allowed."
    INVALID_IMAGE_TYPE = "Invalid image type. Only JPEG, PNG, and WebP are allowed."
    INVALID_IMAGE = "Invalid image data."
    USER_UPDATE_FAILED = "Failed to update user."
    USER_FETCH_FAILED = "Failed to fetch user."
    OSHI_UPDATE_FAILED = "Failed to update oshi."
    PUBLIC_STATUS_UPDATE_FAILED = "Failed to update public status."
    PROFILE_STATS_FETCH_ERROR = "Failed to fetch profile statistics."
    OSHI_LIMIT_REACHED = "You can only have up to 5 oshis."
    OSHI_ALREADY_EXISTS = "This oshi is already in your list."
    OSHI_NOT_FOUND = "Oshi not found in your list."


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
    PUBLIC_USER_NOT_FOUND = "User not found or private"
    IMAGE_TOO_LARGE = "Image is too large"
    INVALID_IMAGE_TYPE = "Invalid image type"
    INVALID_IMAGE = "Invalid image data"
    USER_UPDATE_FAILED = "Failed to update user"
    USER_FETCH_FAILED = "Failed to fetch user"
    OSHI_UPDATE_FAILED = "Failed to update oshi"
    OSHI_LIMIT_REACHED = "You can only have up to 5 oshis"
    OSHI_ALREADY_EXISTS = "This oshi is already in your list"
    OSHI_NOT_FOUND = "Oshi not found in your list"
    PUBLIC_STATUS_UPDATE_FAILED = "Failed to update public status"
    PROFILE_STATS_FETCH_FAILED = "Failed to fetch profile statistics"


class Info:
    USER_CREATED = "Register success."
    USER_CREATED_WITH_EMAIL = (
        "Register success. Please check your email for verification link."
    )
    OSHI_ADDED = "Oshi added successfully."
    OSHI_REMOVED = "Oshi removed successfully."
    PUBLIC_STATUS_UPDATED = "Public status updated successfully."
    PROFILE_PICTURE_UPDATED = "Profile picture updated successfully."
    PROFILE_UPDATED = "Profile updated successfully."


class RankConfig:
    """Configuration for user rank/level calculation."""

    MILESTONES = [
        {"xp": 0, "title": "Newcomer"},
        {"xp": 1, "title": "First Step"},
        {"xp": 10, "title": "Regular Visitor"},
        {"xp": 50, "title": "Dedicated Fan"},
        {"xp": 100, "title": "Century Club"},
        {"xp": 150, "title": "Theater Icon"},
        {"xp": 200, "title": "Legendary Wota"},
        {"xp": 300, "title": "Theater Kami"},
        {"xp": 500, "title": "Absolute Legend"},
    ]
