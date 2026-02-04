from fastapi import APIRouter, Depends, status

from src.dependencies import get_current_user, get_feedback_service, require_admin
from src.feedback.schemas import (
    FeedbackCreate,
    FeedbackPaginationResponse,
    FeedbackResponse,
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
):
    """Submit new feedback"""
    return await service.create_feedback(feedback)


@router.get(
    "",
    response_model=FeedbackPaginationResponse,
)
async def get_feedback(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_admin),
    service: FeedbackService = Depends(get_feedback_service),
):
    """Get all feedback (Admin only)"""
    return await service.get_all_feedback(page, limit)
