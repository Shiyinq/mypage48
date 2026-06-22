from src.exceptions import DomainException
from src.tickets.constants import DomainErrorCode


class TicketNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_NOT_FOUND


class TicketCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_CREATION_FAILED


class TicketUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_UPDATE_FAILED


class TicketDeletionError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_DELETION_FAILED


class TicketFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_FETCH_FAILED


class ImageTooLargeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.IMAGE_TOO_LARGE


class InvalidImageTypeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_IMAGE_TYPE


class InvalidImageError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_IMAGE


class InvalidPhotoTypeError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.INVALID_PHOTO_TYPE
