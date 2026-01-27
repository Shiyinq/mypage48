from src.feedback.repository import FeedbackRepository
from src.feedback.schemas import FeedbackCreate, FeedbackResponse
from src.feedback.exceptions import FeedbackCreationError, FeedbackFetchError


class FeedbackService:
    def __init__(self, repository: FeedbackRepository):
        self.repository = repository

    async def create_feedback(self, feedback_data: FeedbackCreate) -> FeedbackResponse:
        try:
            result = await self.repository.create(feedback_data)
            return FeedbackResponse(**result)
        except Exception as e:
            raise FeedbackCreationError(original_exception=e)

    async def get_all_feedback(self, page: int = 1, limit: int = 20) -> dict:
        try:
            skip = (page - 1) * limit
            results = await self.repository.find_all(skip, limit)
            total = await self.repository.count()
            
            data = [FeedbackResponse(**r) for r in results]
            
            return {
                "data": data,
                "page": page,
                "limit": limit,
                "total": total,
                "has_more": (skip + limit) < total
            }
        except Exception as e:
            raise FeedbackFetchError(original_exception=e)
