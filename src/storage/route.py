import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src import dependencies
from src.auth.schemas import UserCurrent
from src.dependencies import get_storage_service
from src.logging_config import create_logger
from src.storage.schemas import (
    ImageUploadRequest,
    ImageUploadResponse,
    PresignedUrlResponse,
)
from src.storage.service import StorageService

router = APIRouter()

logger = create_logger("storage", __name__)


@router.get("/storage/external/{path:path}")
async def proxy_external_media(path: str):
    """
    Proxy media files from jkt48.com to bypass cross-site blocking.

    Forwards the request to https://jkt48.com/api/v1/storages/{path}
    and returns the response with appropriate headers.
    """
    path = path.lstrip("/")
    upstream_url = f"https://jkt48.com/api/v1/storages/{path}"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            upstream_response = await client.get(upstream_url)

        if upstream_response.status_code != 200:
            logger.warning(
                f"Upstream returned {upstream_response.status_code} for {path}"
            )
            return Response(
                status_code=upstream_response.status_code,
                content=upstream_response.content,
            )

        content_type = upstream_response.headers.get("content-type", "image/jpeg")

        return Response(
            content=upstream_response.content,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
            },
        )
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching external media: {path}")
        return Response(status_code=504, content=b"Gateway Timeout")
    except Exception as e:
        logger.error(f"Error proxying external media: {e}")
        return Response(status_code=502, content=b"Bad Gateway")


@router.post("/storage/upload", status_code=201, response_model=ImageUploadResponse)
async def upload_image(
    request: ImageUploadRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Upload an image to storage.

    Accepts base64 encoded image and category.
    Returns filename and presigned URL.
    """
    result = storage_service.upload_image(
        user_id=current_user.userId,
        base64_image=request.image,
        category=request.category,
    )
    logger.info(f"Image uploaded: {result.filename}")
    return result


@router.get("/storage/url/{filename:path}", response_model=PresignedUrlResponse)
async def get_presigned_url(
    filename: str,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get a presigned URL for an image.

    Returns URL with expiration time.
    """
    return storage_service.get_presigned_url(filename)
