from src.exceptions import DomainException
from src.theater.constants import DomainErrorCode


class TicketNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_NOT_FOUND


class TicketCreationError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_CREATION_FAILED


class TicketUpdateError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_UPDATE_FAILED


class TicketDeletionError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.TICKET_DELETION_FAILED
