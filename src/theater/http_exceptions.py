from src.http_exceptions import InternalServerError, NotFound
from src.theater.constants import ErrorCode


class TicketNotFound(NotFound):
    DETAIL = ErrorCode.TICKET_NOT_FOUND


class TicketCreateError(InternalServerError):
    DETAIL = ErrorCode.TICKET_CREATION_FAILED


class TicketUpdateError(InternalServerError):
    DETAIL = ErrorCode.TICKET_UPDATE_FAILED


class TicketDeleteError(InternalServerError):
    DETAIL = ErrorCode.TICKET_DELETION_FAILED
