from typing import Any, Dict

from src.config import Settings
from src.logging_config import create_logger
from src.news.exceptions import NewsFetchError, NewsItemFetchError, NewsNotFoundError
from src.news.repository import NewsRepository

logger = create_logger("news_service", __name__)


class NewsService:
    def __init__(
        self,
        repository: NewsRepository,
        config: Settings,
    ):
        self.repository = repository
        self.config = config

    async def get_news(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        try:
            return await self.repository.get_news(page=page, limit=limit)
        except Exception as e:
            logger.exception(f"Error fetching news: {str(e)}")
            raise NewsFetchError()

    async def get_news_by_link(self, link: str) -> Dict[str, Any]:
        try:
            news = await self.repository.get_news_by_link(link)
            if not news:
                raise NewsNotFoundError()
            return news
        except NewsNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching news by link: {str(e)}")
            raise NewsItemFetchError()
