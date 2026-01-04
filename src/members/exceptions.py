from src.exceptions import DomainException
from src.members.constants import DomainErrorCode


class MemberNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.MEMBER_NOT_FOUND


class MemberFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.MEMBER_FETCH_FAILED
