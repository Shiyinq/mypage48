from src.exceptions import DomainException
from src.link_resolver.constants import DomainErrorCode


class InvalidLinkError(DomainException):
    """The URL is not an allowed short link, or fails validation."""

    ERROR_MESSAGE = DomainErrorCode.INVALID_LINK


class LinkResolveError(DomainException):
    """The short link could not be resolved to a canonical URL."""

    ERROR_MESSAGE = DomainErrorCode.RESOLVE_FAILED
