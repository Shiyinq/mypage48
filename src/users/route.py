from fastapi import APIRouter, Depends

from src import dependencies
from src.auth.schemas import UserCurrent
from src.dependencies import get_user_service
from src.logging_config import create_logger
from src.users.schemas import (
    UserCreatedWithEmail,
    UserCreateRequest,
    UserCreateResponse,
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


@router.get("/users/profile", response_model=UserCurrent)
async def user_profile(current_user=Depends(dependencies.get_current_user)):
    """
    Get the profile information of the currently logged-in user.

    Returns:
        UserCurrent: The current user's profile data.
    """

    return current_user
