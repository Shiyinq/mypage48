from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api_keys.schemas import APIKeysResponse
from src.api_keys.service import ApiKeyService
from src.config import config
from src.dependencies import (
    get_api_key_service,
    get_current_user,
    require_csrf_protection,
)
from src.logging_config import create_logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

logger = create_logger("api_keys", __name__)


@router.post("/key", status_code=201, response_model=APIKeysResponse)
@limiter.limit(f"{config.auth_requests_per_minute}/minute")
async def create_api_key(
    request: Request,
    current_user=Depends(get_current_user),
    _=Depends(require_csrf_protection),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """
    Create a new API key for the current user.

    Returns:
        APIKeysResponse: Newly generated API key and detail message.
    """
    new_api_key = await service.create_api_key(current_user.userId)
    return new_api_key


@router.delete("/key", status_code=200, response_model=APIKeysResponse)
async def delete_api_key(
    current_user=Depends(get_current_user),
    _=Depends(require_csrf_protection),
    service: ApiKeyService = Depends(get_api_key_service),
):
    """
    Delete the current user's API key.

    Returns:
        APIKeysResponse: Confirmation message after deleting the API key.

    Raises:
        APIKeyNotFound: If the current user does not have an API key.
    """
    deleted = await service.delete_api_key(current_user.userId)

    logger.info(f"Success: user_id={current_user.userId}")
    return deleted
