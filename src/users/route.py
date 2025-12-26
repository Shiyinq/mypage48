from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src import dependencies
from src.auth.schemas import UserCurrent, OshiResponse
from src.dependencies import get_user_service, get_member_service
from src.logging_config import create_logger
from src.users.schemas import (
    UserCreatedWithEmail,
    UserCreateRequest,
    UserCreateResponse,
)
from src.users.service import UserService
from src.members.service import MemberService

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


@router.get("/users/profile", response_model=UserCurrent)
async def user_profile(
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    member_service: MemberService = Depends(get_member_service),
):
    """
    Get the profile information of the currently logged-in user.

    Returns:
        UserCurrent: The current user's profile data.
    """

    oshi_response = None

    if current_user.oshiId:
        try:
            member_detail = await member_service.get_member_by_id(current_user.oshiId)
            member = member_detail.member
            oshi_response = OshiResponse(
                name=member.name,
                nickname=member.nickname,
                generation=member.generation or "-",
                profilePicture=member.img or "https://upload.wikimedia.org/wikipedia/commons/8/82/JKT48.svg",
                catchphrase=member.jiko or "-",
                socials=member.socials.model_dump() if member.socials else None
            )
        except Exception as e:
            logger.warning(f"Failed to fetch oshi data for id {current_user.oshiId}: {e}")

    current_user.oshi = oshi_response
    return current_user


class UpdateOshiRequest(BaseModel):
    oshiId: int


@router.post("/users/oshi", status_code=200)
async def update_oshi(
    request: UpdateOshiRequest,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the user's Oshi.
    """
    await user_service.update_oshi(current_user.userId, request.oshiId)
    return {"message": "Oshi updated successfully"}
