from fastapi import APIRouter, Depends, Query

from src.dependencies import get_news_service
from src.news.schemas import NewsPaginationResponse, NewsResponse
from src.news.service import NewsService

router = APIRouter()


@router.get("/", response_model=NewsPaginationResponse)
async def get_news(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    service: NewsService = Depends(get_news_service),
):
    """Get latest news."""
    return await service.get_news(page=page, limit=limit)


@router.get("/{link}", response_model=NewsResponse)
async def get_news_by_link(
    link: str,
    service: NewsService = Depends(get_news_service),
):
    """Get a single news item by link."""
    return await service.get_news_by_link(link)
