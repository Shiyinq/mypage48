from fastapi import APIRouter, Depends, status

from src.dependencies import get_feedback_service, require_admin
from src.feedback.schemas import FeedbackCreate, FeedbackResponse, FeedbackPaginationResponse
from src.feedback.service import FeedbackService


router = APIRouter()

@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    description="Submit new feedback"
)
async def submit_feedback(
    feedback: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service)
):
    return await service.create_feedback(feedback)


@router.get(
    "",
    response_model=FeedbackPaginationResponse,
    description="Get all feedback (Admin only)"
)
async def get_feedback(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_admin),
    service: FeedbackService = Depends(get_feedback_service)
):
    return await service.get_all_feedback(page, limit)
