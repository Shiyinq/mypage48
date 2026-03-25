from fastapi import APIRouter, Depends, Request, Response
from src.live.schemas import LiveResponse, LiveStreamingURL, LiveStreamInfo
from src.live.service import LiveService
from src.dependencies import get_live_service
from typing import List

from slowapi import Limiter
from slowapi.util import get_remote_address
from src.config import config

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("", response_model=LiveResponse)
async def get_live_status(
    service: LiveService = Depends(get_live_service)
):
    """Get summarized live status from Showroom and IDN"""
    return await service.get_live_status()

@router.get("/proxy")
@limiter.limit(f"{config.LIVE_PROXY_REQUESTS_PER_MINUTE}/minute")
async def proxy_streaming_data(
    request: Request,
    url: str,
    service: LiveService = Depends(get_live_service)
):
    """Proxy streaming data (m3u8, ts) to bypass CORS"""
    proxy_res = await service.proxy_hls_request(url)
    return Response(
        content=proxy_res.get("content"),
        status_code=proxy_res.get("status_code", 200),
        media_type=proxy_res.get("media_type"),
        headers=proxy_res.get("headers")
    )

@router.get("/showroom/comments")
@limiter.limit(f"{config.LIVE_PROXY_REQUESTS_PER_MINUTE}/minute")
async def get_showroom_comments(
    request: Request,
    room_id: str,
    service: LiveService = Depends(get_live_service)
):
    """Get showroom comments via proxy to bypass CORS"""
    return await service.get_showroom_comments(room_id)

@router.get("/{platform}/{id}/streaming-url", response_model=LiveStreamInfo)
async def get_streaming_url(
    platform: str,
    id: str,
    service: LiveService = Depends(get_live_service)
):
    """Get streaming URL for a specific room/live"""
    return await service.get_streaming_url(platform, id)
