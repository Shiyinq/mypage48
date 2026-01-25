from fastapi import APIRouter, Depends

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
