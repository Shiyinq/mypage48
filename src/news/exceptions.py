from src.exceptions import DomainException
from src.news.constants import DomainErrorCode


class NewsNotFoundError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.NEWS_NOT_FOUND


class NewsFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.NEWS_FETCH_ERROR


class NewsItemFetchError(DomainException):
    ERROR_MESSAGE = DomainErrorCode.NEWS_ITEM_FETCH_ERROR
