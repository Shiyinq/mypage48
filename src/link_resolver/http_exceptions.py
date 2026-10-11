from src.http_exceptions import BadRequest, UnprocessableContent
from src.link_resolver.constants import ErrorCode


class InvalidLink(BadRequest):
    DETAIL = ErrorCode.INVALID_LINK


class LinkResolveFailed(UnprocessableContent):
    DETAIL = ErrorCode.RESOLVE_FAILED
