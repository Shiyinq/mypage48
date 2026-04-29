from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.auth.schemas import UserCurrent
from src.dependencies import (
    get_current_user,
    get_export_service,
    require_csrf_protection,
)
from src.export.schemas import ExportResponse
from src.export.service import ExportService

router = APIRouter()


@router.get("/status", response_model=ExportResponse)
async def get_export_status(
    current_user: UserCurrent = Depends(get_current_user),
    service: ExportService = Depends(get_export_service),
):
    """Get the status of the data export job."""
    return await service.get_status(current_user.userId)


@router.post("", response_model=ExportResponse)
async def initiate_export(
    current_user: UserCurrent = Depends(get_current_user),
    service: ExportService = Depends(get_export_service),
    _=Depends(require_csrf_protection),
):
    """Initiate a data export job."""
    return await service.initiate_export(current_user.userId)


@router.get("/download")
async def download_export(
    current_user: UserCurrent = Depends(get_current_user),
    service: ExportService = Depends(get_export_service),
):
    """Download the exported data. This will delete the file after download."""

    stream, filename, cleanup = await service.download_export(current_user.userId)

    from starlette.background import BackgroundTask

    return StreamingResponse(
        stream,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
        background=BackgroundTask(cleanup),
    )
