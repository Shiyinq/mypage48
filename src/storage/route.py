from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse

from src import dependencies
from src.auth.schemas import UserCurrent
from src.dependencies import get_storage_service
from src.logging_config import create_logger
from src.storage.schemas import (
    BatchPresignedUrlRequest,
    BatchPresignedUrlResponse,
    ImageUploadRequest,
    ImageUploadResponse,
    PresignedUrlResponse,
)
from src.storage.service import StorageService

router = APIRouter()

logger = create_logger("storage", __name__)


@router.get("/storage/m/{path:path}")
async def proxy_storage_media(
    path: str,
    expires: str | None = Query(None, description="Expiration timestamp"),
    signature: str
    | None = Query(None, description="HMAC signature of the path and expiration"),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Proxy internal media files from MinIO.
    This behaves like an S3 Presigned URL but is served through our backend proxy.

    Security logic:
    1. Verify that the signature matches the path and expiration time.
    2. Verify that the current time is before the expiration time.
    3. Return X-Robots-Tag: noindex to prevent search engine indexing.
    """
    if (
        not expires
        or not signature
        or not storage_service.verify_signature(path, expires, signature)
    ):
        return Response(content="Unauthorized access or expired link", status_code=401)

    content, media_type, status_code = await storage_service.get_internal_media(path)

    if status_code != 200:
        return Response(content=content, status_code=status_code, media_type=media_type)

    return StreamingResponse(
        content=content,
        status_code=status_code,
        media_type=media_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "X-Robots-Tag": "noindex, nofollow, noarchive",
        },
    )


@router.get("/storage/external/{path:path}")
async def proxy_external_media(
    path: str,
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Proxy media files from jkt48.com with local caching in MinIO.

    Checks if the file is in local storage (MinIO) first.
    If not, fetches from https://jkt48.com/api/v1/storages/{path}
    and saves to MinIO for future requests.
    """
    content, media_type, status_code = await storage_service.get_external_media(path)

    if status_code != 200:
        return Response(content=content, status_code=status_code, media_type=media_type)

    return StreamingResponse(
        content=content,
        status_code=status_code,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=3600",
        },
    )


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
    result = await storage_service.upload_image(
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
    return await storage_service.get_presigned_url(filename)


@router.post("/storage/presign/bulk", response_model=BatchPresignedUrlResponse)
async def get_bulk_presigned_urls(
    request: BatchPresignedUrlRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get presigned URLs for multiple images in bulk.
    """
    return await storage_service.get_bulk_presigned_urls(request.filenames)
