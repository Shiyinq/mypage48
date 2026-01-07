class Info:
    IMAGE_UPLOADED = "Image uploaded successfully."
    IMAGE_DELETED = "Image deleted successfully."


class ErrorCode:
    STORAGE_CONNECTION_FAILED = "Failed to connect to storage service."
    IMAGE_UPLOAD_FAILED = "Failed to upload image."
    IMAGE_NOT_FOUND = "Image not found."
    PRESIGNED_URL_FAILED = "Failed to generate image URL."
    INVALID_CATEGORY = "Invalid image category."


class DomainErrorCode:
    STORAGE_CONNECTION_FAILED = "Storage connection failed"
    IMAGE_UPLOAD_FAILED = "Image upload failed"
    IMAGE_NOT_FOUND = "Image not found"
    PRESIGNED_URL_FAILED = "Presigned URL generation failed"
    INVALID_CATEGORY = "Invalid image category"
