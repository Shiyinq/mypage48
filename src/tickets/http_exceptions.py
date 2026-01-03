from src.http_exceptions import BadRequest, InternalServerError, NotFound
from src.tickets.constants import ErrorCode


class TicketNotFound(NotFound):
    DETAIL = ErrorCode.TICKET_NOT_FOUND


class TicketCreateError(InternalServerError):
    DETAIL = ErrorCode.TICKET_CREATION_FAILED


class TicketUpdateError(InternalServerError):
    DETAIL = ErrorCode.TICKET_UPDATE_FAILED


class TicketDeleteError(InternalServerError):
    DETAIL = ErrorCode.TICKET_DELETION_FAILED


class TicketFetchError(InternalServerError):
    DETAIL = ErrorCode.TICKET_FETCH_FAILED


class ImageTooLarge(BadRequest):
    DETAIL = ErrorCode.IMAGE_TOO_LARGE


class InvalidImageType(BadRequest):
    DETAIL = ErrorCode.INVALID_IMAGE_TYPE


class InvalidImage(BadRequest):
    DETAIL = ErrorCode.INVALID_IMAGE
