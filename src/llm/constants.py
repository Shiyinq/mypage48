class Info:
    IMAGE_ANALYZED = "Image analyzed successfully."


class ErrorCode:
    ANALYSIS_FAILED = "Failed to analyze image."
    INVALID_IMAGE = "Invalid image format."
    IMAGE_TOO_LARGE = "Image is too large. Maximum 3MB allowed."
    INVALID_IMAGE_TYPE = "Invalid image type. Only JPEG, PNG, and WebP are allowed."


class DomainErrorCode:
    ANALYSIS_FAILED = "Failed to analyze image."
    IMAGE_TOO_LARGE = "Image is too large"
    INVALID_IMAGE_TYPE = "Invalid image type"
    INVALID_IMAGE = "Invalid image data"
