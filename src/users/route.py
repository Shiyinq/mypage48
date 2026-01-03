from fastapi import APIRouter, Depends

from src import dependencies
from src.auth.schemas import UserCurrent
from src.dependencies import get_user_service
from src.logging_config import create_logger
from src.users.schemas import (
    UserCreatedWithEmail,
    UserCreateRequest,
    UserCreateResponse,
    PublicUserResponse,
    UpdateProfilePictureRequest,
    UpdateOshiRequest,
    UpdatePublicStatusRequest,
    MessageResponse,
    ProfileFullResponse,
)
from src.users.service import UserService

router = APIRouter()

logger = create_logger("users", __name__)


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
):
    """
    Get the complete profile information of the currently logged-in user.

    Returns:
        ProfileFullResponse: Complete profile with all sections:
            - profile: Basic user info
            - oshi: Selected oshi member details
            - rank: Current rank and XP progress
            - stats: Total shows and achievements count
            - oshiTwoShots: 2-shot counts with oshi
            - recentActivity: 5 most recent shows
    """
    return await user_service.get_profile_full(current_user)


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
    return await user_service.update_public_status(current_user.userId, request.isPublic, request.publicYear)


@router.post("/users/profile-picture", status_code=200, response_model=MessageResponse)
async def update_profile_picture(
    request: UpdateProfilePictureRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the user's profile picture.
    """
    return await user_service.update_profile_picture(current_user.userId, request.profilePicture)


@router.get("/u/{username}", response_model=PublicUserResponse)
async def get_public_profile(
    username: str,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a user's public profile by username.
    """
    return await user_service.get_public_profile(username)
