from fastapi import APIRouter, Depends
from src.live.schemas import LiveResponse, LiveStreamingURL, LiveStreamInfo
from src.live.service import LiveService
from src.dependencies import get_live_service
from typing import List

router = APIRouter()

@router.get("", response_model=LiveResponse)
async def get_live_status(
    service: LiveService = Depends(get_live_service)
):
    """Get summarized live status from Showroom and IDN"""
    return await service.get_live_status()

@router.get("/proxy")
async def proxy_streaming_data(
    url: str,
    service: LiveService = Depends(get_live_service)
):
    """Proxy streaming data (m3u8, ts) to bypass CORS"""
    return await service.proxy_hls_request(url)

@router.get("/showroom/comments")
async def get_showroom_comments(
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
