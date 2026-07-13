import typing

from fastapi import APIRouter, Depends, Request, Response

from src.auth.schemas import UserCurrent
from src.config import config
from src.dependencies import get_current_user_optional, get_live_service
from src.limiter import limiter
from src.live.schemas import LiveResponse, LiveStreamInfo
from src.live.service import LiveService

router = APIRouter()


@router.get("", response_model=LiveResponse)
async def get_live_status(service: LiveService = Depends(get_live_service)):
    """Get summarized live status from Showroom and IDN"""
    return await service.get_live_status()


@router.get("/scheduled", response_model=LiveResponse)
async def get_scheduled_live_status(service: LiveService = Depends(get_live_service)):
    """Get scheduled premium live status from IDN"""
    return await service.get_scheduled_premium_lives()


@router.get("/proxy")
@limiter.limit(
    f"{config.live_proxy_requests_per_minute}/minute", override_defaults=True
)
async def proxy_streaming_data(
    request: Request, url: str, service: LiveService = Depends(get_live_service)
):
    """Proxy streaming data (m3u8, ts) to bypass CORS"""
    proxy_res = await service.proxy_hls_request(url)
    return Response(
        content=proxy_res.get("content"),
        status_code=proxy_res.get("status_code", 200),
        media_type=proxy_res.get("media_type"),
        headers=proxy_res.get("headers"),
    )


@router.get("/showroom/comments")
@limiter.limit(
    f"{config.live_proxy_requests_per_minute}/minute", override_defaults=True
)
async def get_showroom_comments(
    request: Request, room_id: str, service: LiveService = Depends(get_live_service)
):
    """Get showroom comments via proxy to bypass CORS"""
    actual_room_id = room_id.split("-")[0] if "-" in room_id else room_id
    return await service.get_showroom_comments(actual_room_id)


@router.get("/showroom/gifts")
@limiter.limit(
    f"{config.live_proxy_requests_per_minute}/minute", override_defaults=True
)
async def get_showroom_gifts(
    request: Request, room_id: str, service: LiveService = Depends(get_live_service)
):
    """Get showroom gift log via proxy to bypass CORS"""
    actual_room_id = room_id.split("-")[0] if "-" in room_id else room_id
    return await service.get_showroom_gifts(actual_room_id)


@router.get("/showroom/gift-list")
@limiter.limit(
    f"{config.live_proxy_requests_per_minute}/minute", override_defaults=True
)
async def get_showroom_gift_list(
    request: Request, room_id: str, service: LiveService = Depends(get_live_service)
):
    """Get showroom gift list via proxy to bypass CORS"""
    actual_room_id = room_id.split("-")[0] if "-" in room_id else room_id
    return await service.get_showroom_gift_list(actual_room_id)


@router.get("/{platform}/{id}/streaming-url", response_model=LiveStreamInfo)
async def get_streaming_url(
    platform: str,
    id: str,
    current_user: typing.Optional[UserCurrent] = Depends(get_current_user_optional),
    service: LiveService = Depends(get_live_service),
):
    """Get streaming URL for a specific room/live"""
    return await service.get_streaming_url(platform, id, current_user)
