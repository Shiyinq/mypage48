from fastapi import APIRouter, Depends, Query, status

from src.dependencies import (
    get_current_user,
    get_feedback_service,
    require_admin,
    require_csrf_protection,
)
from src.feedback.constants import FeedbackStatus
from src.feedback.schemas import (
    FeedbackCreate,
    FeedbackPaginationResponse,
    FeedbackResponse,
    FeedbackUpdateStatus,
)
from src.feedback.service import FeedbackService

router = APIRouter()


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user=Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
    _=Depends(require_csrf_protection),
):
    """Submit new feedback"""
    return await service.create_feedback(
        feedback,
        user_id=current_user.userId,
        user_name=current_user.name,
        user_email=current_user.email,
    )


@router.get(
    "/me",
    response_model=FeedbackPaginationResponse,
)
async def get_my_feedback(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
):
    """Get current user's feedback"""
    return await service.get_user_feedback(current_user.userId, page, limit)


@router.get(
    "",
    response_model=FeedbackPaginationResponse,
)
async def get_feedback(
    page: int = 1,
    limit: int = 20,
    status: list[FeedbackStatus] | None = Query(default=None),
    current_user=Depends(require_admin),
    service: FeedbackService = Depends(get_feedback_service),
):
    """Get all feedback (Admin only)"""
    return await service.get_all_feedback(page, limit, status)


@router.patch(
    "/{feedback_id}/status",
    response_model=FeedbackResponse,
)
async def update_feedback_status(
    feedback_id: str,
    update_data: FeedbackUpdateStatus,
    current_user=Depends(require_admin),
    service: FeedbackService = Depends(get_feedback_service),
    _=Depends(require_csrf_protection),
):
    """Update feedback status and add notes (Admin only)"""
    return await service.update_feedback_status(feedback_id, update_data)


@router.delete(
    "/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_feedback(
    feedback_id: str,
    current_user=Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
    _=Depends(require_csrf_protection),
):
    """Delete a feedback (Owner only)"""
    await service.delete_feedback(feedback_id, current_user.userId)
    return None
