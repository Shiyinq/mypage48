import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from src.auth.schemas import UserCurrent
from src.dependencies import (
    get_current_user_optional,
    get_replay_service,
    require_admin,
)
from src.replay.exceptions import ReplayNotFound, ReplayUploadError
from src.replay.schemas import (
    ReplayDetailResponse,
    ReplayListItem,
    ReplayResponse,
    ReplayUpdateYouTube,
)
from src.replay.service import ReplayService

router = APIRouter()


@router.post("/admin/replay/upload", response_model=ReplayResponse)
async def upload_replay(
    metadata: str = Form(..., description="JSON string of recording metadata"),
    jsonl: UploadFile = File(..., description="Chat JSONL file"),
    srt: UploadFile = File(..., description="Subtitle SRT file"),
    thumbnail: Optional[UploadFile] = File(None, description="Thumbnail JPG"),
    screenshots: list[UploadFile] = File(
        default_factory=list, description="Screenshot files"
    ),
    _=Depends(require_admin),
    service: ReplayService = Depends(get_replay_service),
):
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        raise ReplayUploadError("Invalid metadata JSON")

    live_id = meta.get("live_id")
    if not live_id:
        raise ReplayUploadError("metadata.live_id is required")

    thumbnail_bytes = await thumbnail.read() if thumbnail else None
    jsonl_bytes = await jsonl.read()
    srt_bytes = await srt.read()

    screenshot_list = []
    for sf in screenshots:
        data = await sf.read()
        screenshot_list.append((sf.filename or "screenshot.jpg", data))

    return await service.upload(
        live_id=live_id,
        metadata_bytes=metadata.encode(),
        thumbnail_bytes=thumbnail_bytes,
        jsonl_bytes=jsonl_bytes,
        srt_bytes=srt_bytes,
        screenshot_bytes_list=screenshot_list,
    )


@router.patch("/admin/replay/{live_id}/youtube")
async def update_youtube_data(
    live_id: str,
    data: ReplayUpdateYouTube,
    _=Depends(require_admin),
    service: ReplayService = Depends(get_replay_service),
):
    success = await service.update_youtube_data(
        live_id, data.youtube_id, data.youtube_title
    )
    if not success:
        raise ReplayNotFound()
    return {"status": "ok"}


@router.get("/replays", response_model=list[ReplayListItem])
async def list_replays(
    current_user: UserCurrent | None = Depends(get_current_user_optional),
    service: ReplayService = Depends(get_replay_service),
):
    docs = await service.list_all(current_user=current_user)
    return [ReplayListItem(**d) for d in docs]


@router.get("/replays/{live_id}", response_model=ReplayDetailResponse)
async def get_replay_detail(
    live_id: str,
    service: ReplayService = Depends(get_replay_service),
):
    doc = await service.get_detail(live_id)
    if not doc:
        raise ReplayNotFound()
    return doc


@router.get("/replays/{live_id}/srt")
async def get_replay_srt(
    live_id: str,
    service: ReplayService = Depends(get_replay_service),
):
    content = await service.get_srt_content(live_id)
    if content is None:
        raise ReplayNotFound()
    return Response(content=content, media_type="text/plain")
