from src.exceptions import DomainException

class LiveHistoryNotFoundError(DomainException):
    pass

class LiveHistoryUpdateError(DomainException):
    pass
