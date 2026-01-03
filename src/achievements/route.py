from fastapi import APIRouter, Depends

from src import dependencies
from src.auth.schemas import UserCurrent
from src.dependencies import get_achievements_service
from src.achievements.service import AchievementsService
from src.achievements.schemas import AchievementsResponse

router = APIRouter()


@router.get("", response_model=AchievementsResponse)
async def get_achievements(
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    achievements_service: AchievementsService = Depends(get_achievements_service),
):
    """
    Get all achievements with unlock status and progress.

    Returns:
        AchievementsResponse: All achievements with counts.
    """
    return await achievements_service.get_achievements(current_user.userId)
