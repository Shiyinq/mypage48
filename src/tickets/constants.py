class Info:
    TICKET_CREATED = "Ticket created successfully."
    TICKET_UPDATED = "Ticket updated successfully."
    TICKET_DELETED = "Ticket deleted successfully."


class ErrorCode:
    TICKET_NOT_FOUND = "Ticket not found."
    TICKET_CREATION_FAILED = "Failed to create ticket."
    TICKET_UPDATE_FAILED = "Failed to update ticket."
    TICKET_DELETION_FAILED = "Failed to delete ticket."
    TICKET_FETCH_FAILED = "Failed to fetch ticket."
    IMAGE_TOO_LARGE = "Image is too large. Maximum 3MB allowed."
    INVALID_IMAGE_TYPE = "Invalid image type. Only JPEG, PNG, and WebP are allowed."
    INVALID_IMAGE = "Invalid image data."
    INVALID_PHOTO_TYPE = "Invalid photo type. Must be 'ticket' or 'twoshot'."


class DomainErrorCode:
    TICKET_NOT_FOUND = "Ticket not found."
    TICKET_CREATION_FAILED = "Failed to create ticket."
    TICKET_UPDATE_FAILED = "Failed to update ticket."
    TICKET_DELETION_FAILED = "Failed to delete ticket."
    TICKET_FETCH_FAILED = "Failed to fetch ticket."
    IMAGE_TOO_LARGE = "Image is too large"
    INVALID_IMAGE_TYPE = "Invalid image type"
    INVALID_IMAGE = "Invalid image data"
    INVALID_PHOTO_TYPE = "Invalid photo type"
