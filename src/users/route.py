from fastapi import APIRouter, Depends, Query
from typing import Optional

from src import dependencies
from src.auth.schemas import UserCurrent
from src.dependencies import get_user_service, get_storage_service, require_admin
from src.logging_config import create_logger
from src.storage.service import StorageService
from src.users.schemas import (
    MessageResponse,
    ProfileFullResponse,
    PublicUserResponse,
    UpdateOshiRequest,
    UpdateProfilePictureRequest,
    UpdatePublicStatusRequest,
    UserCreatedWithEmail,
    UserCreateRequest,
    UserCreateResponse,
    UserListResponse,
)
from src.users.service import UserService

logger = create_logger("users", __name__)

router = APIRouter()


@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Search by name, email, or username"),
    _: UserCurrent = Depends(require_admin),
    service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get all registered users (admin only).

    - **page**: Page number (default 1)
    - **limit**: Items per page (default 20, max 100)
    - **search**: Search by name, email, or username
    """
    result = await service.get_all_users(page, limit, search)
    
    # Resolve profile pictures to presigned URLs
    for user in result.data:
        if user.profilePicture:
            user.profilePicture = storage_service.resolve_url(user.profilePicture)
    
    return result



@router.post("/users/signup", status_code=201, response_model=UserCreateResponse)
async def signup(
    user: UserCreateRequest, user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user account.
    """

    result = await user_service.create_user(user)

    if isinstance(result, UserCreatedWithEmail):
        logger.info("User created successfully and verification email sent")
    else:
        logger.info("User created successfully")

    return result


@router.get("/users/profile", response_model=ProfileFullResponse)
async def user_profile(
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get the complete profile information of the currently logged-in user.
    """
    profile = await user_service.get_profile_full(current_user)
    return storage_service.resolve_profile_full_images(profile)


@router.post("/users/oshi", status_code=200, response_model=MessageResponse)
async def update_oshi(
    request: UpdateOshiRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the user's Oshi.
    """
    return await user_service.update_oshi(current_user.userId, request.oshiId)


@router.post("/users/public-status", status_code=200, response_model=MessageResponse)
async def update_public_status(
    request: UpdatePublicStatusRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the user's public profile status.
    """
    return await user_service.update_public_status(
        current_user.userId, request.isPublic, request.publicYear
    )


@router.post("/users/profile-picture", status_code=200, response_model=MessageResponse)
async def update_profile_picture(
    request: UpdateProfilePictureRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the user's profile picture.
    """
    return await user_service.update_profile_picture(
        current_user.userId, request.profilePicture
    )


@router.get("/u/{username}", response_model=PublicUserResponse)
async def get_public_profile(
    username: str,
    user_service: UserService = Depends(get_user_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get a user's public profile by username.
    """
    profile = await user_service.get_public_profile(username)
    return storage_service.resolve_public_user_images(profile)
