from typing import Any, Dict, Optional

from src.config import Settings
from src.exceptions import InvalidDateError
from src.logging_config import create_logger
from src.news.exceptions import NewsFetchError, NewsItemFetchError, NewsNotFoundError
from src.news.repository import NewsRepository
from src.storage.service import StorageService
from src.utils import parse_date_range

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

    async def get_news(
        self,
        page: int = 1,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            parsed_start, parsed_end = parse_date_range(start_date, end_date)
            res = await self.repository.get_news(
                page=page, limit=limit, start_date=parsed_start, end_date=parsed_end
            )
            if "data" in res and isinstance(res["data"], list):
                for item in res["data"]:
                    if isinstance(item, dict) and item.get("background_image"):
                        media_res = await self.storage_service.resolve_external_media(
                            item["background_image"]
                        )
                        item["background_image"] = media_res["url"]
                        if media_res.get("blurHash"):
                            item["blurHash"] = media_res["blurHash"]
            return res
        except InvalidDateError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching news: {str(e)}")
            raise NewsFetchError()

    async def get_news_by_link(self, link: str) -> Dict[str, Any]:
        try:
            news = await self.repository.get_news_by_link(link)
            if not news:
                raise NewsNotFoundError()

            if news.get("background_image"):
                media_res = await self.storage_service.resolve_external_media(
                    news["background_image"]
                )
                news["background_image"] = media_res["url"]
                if media_res.get("blurHash"):
                    news["blurHash"] = media_res["blurHash"]

            return news
        except NewsNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching news by link: {str(e)}")
            raise NewsItemFetchError()
