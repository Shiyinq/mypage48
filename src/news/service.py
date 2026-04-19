from typing import Any, Dict

from src.config import Settings
from src.logging_config import create_logger
from src.news.exceptions import NewsFetchError, NewsItemFetchError, NewsNotFoundError
from src.news.repository import NewsRepository
from src.storage.service import StorageService

logger = create_logger("news_service", __name__)


class NewsService:
    def __init__(
        self,
        repository: NewsRepository,
        config: Settings,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.config = config
        self.storage_service = storage_service

    async def get_news(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        try:
            res = await self.repository.get_news(page=page, limit=limit)
            if "data" in res and isinstance(res["data"], list):
                for item in res["data"]:
                    if isinstance(item, dict) and item.get("background_image"):
                        item[
                            "background_image"
                        ] = await self.storage_service.resolve_external_url(
                            item["background_image"]
                        )
            return res
        except Exception as e:
            logger.exception(f"Error fetching news: {str(e)}")
            raise NewsFetchError()

    async def get_news_by_link(self, link: str) -> Dict[str, Any]:
        try:
            news = await self.repository.get_news_by_link(link)
            if not news:
                raise NewsNotFoundError()

            if news.get("background_image"):
                news[
                    "background_image"
                ] = await self.storage_service.resolve_external_url(
                    news["background_image"]
                )

            return news
        except NewsNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching news by link: {str(e)}")
            raise NewsItemFetchError()
