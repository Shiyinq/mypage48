from src.http_exceptions import InternalServerError, NotFound
from src.news.constants import ErrorCode


class NewsNotFound(NotFound):
    DETAIL = ErrorCode.NEWS_NOT_FOUND


class NewsFetchHTTPError(InternalServerError):
    DETAIL = ErrorCode.NEWS_FETCH_ERROR


class NewsItemFetchHTTPError(InternalServerError):
    DETAIL = ErrorCode.NEWS_ITEM_FETCH_ERROR
