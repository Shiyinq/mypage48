from src.auth.email_service import EmailService
from src.feedback.exceptions import (
    FeedbackCreationError,
    FeedbackDeleteError,
    FeedbackFetchError,
    FeedbackNotFound,
    FeedbackUpdateError,
)
from src.feedback.repository import FeedbackRepository
from src.feedback.schemas import FeedbackCreate, FeedbackResponse, FeedbackUpdateStatus
from src.logging_config import create_logger

logger = create_logger("feedback_service", __name__)


class FeedbackService:
    def __init__(self, repository: FeedbackRepository, email_service: EmailService):
        self.repository = repository
        self.email_service = email_service

    async def create_feedback(
        self,
        feedback_data: FeedbackCreate,
        user_id: str = None,
        user_name: str = None,
        user_email: str = None,
    ) -> FeedbackResponse:
        try:
            feedback_dict = feedback_data.model_dump()
            feedback_dict["status"] = "pending"
            if user_id:
                feedback_dict["user_id"] = user_id
            if user_name:
                feedback_dict["name"] = user_name
            if user_email:
                feedback_dict["email"] = user_email

            result = await self.repository.create(feedback_dict)
            return FeedbackResponse(**result)
        except Exception as e:
            logger.exception(f"Error creating feedback: {str(e)}")
            raise FeedbackCreationError()

    async def get_all_feedback(self, page: int = 1, limit: int = 20) -> dict:
        try:
            skip = (page - 1) * limit
            results = await self.repository.find_all(skip, limit)
            total = await self.repository.count()

            data = [FeedbackResponse(**r) for r in results]

            import math

            last_page = math.ceil(total / limit) if total > 0 else 1

            return {
                "data": data,
                "meta": {
                    "current_page": page,
                    "last_page": last_page,
                    "total_data": total,
                    "per_page": limit,
                    "next_page": page + 1 if page < last_page else None,
                },
            }
        except Exception as e:
            logger.exception(f"Error fetching all feedback: {str(e)}")
            raise FeedbackFetchError()

    async def get_user_feedback(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> dict:
        try:
            skip = (page - 1) * limit
            results = await self.repository.find_by_user_id(user_id, skip, limit)
            total = await self.repository.count_by_user_id(user_id)

            data = [FeedbackResponse(**r) for r in results]

            import math

            last_page = math.ceil(total / limit) if total > 0 else 1

            return {
                "data": data,
                "meta": {
                    "current_page": page,
                    "last_page": last_page,
                    "total_data": total,
                    "per_page": limit,
                    "next_page": page + 1 if page < last_page else None,
                },
            }
        except Exception as e:
            logger.exception(f"Error fetching user feedback: {str(e)}")
            raise FeedbackFetchError()

    async def update_feedback_status(
        self, feedback_id: str, update_data: FeedbackUpdateStatus
    ) -> FeedbackResponse:
        try:
            existing = await self.repository.find_by_id(feedback_id)
            if not existing:
                raise FeedbackNotFound()

            update_dict = update_data.model_dump(exclude_unset=True)
            success = await self.repository.update(feedback_id, update_dict)
            if not success:
                raise Exception("Failed to update feedback status")

            # Send email if status changed and email exists
            if update_data.status != existing.get("status") and existing.get("email"):
                name = existing.get("name") or "User"
                await self.email_service.send_feedback_status_update(
                    email=existing["email"],
                    name=name,
                    new_status=update_data.status.value,
                    admin_notes=update_data.admin_notes or "",
                    feedback_message=existing.get("message", ""),
                )

            # Return updated object
            updated = await self.repository.find_by_id(feedback_id)
            if not updated:
                raise FeedbackNotFound()
            return FeedbackResponse(**updated)
        except FeedbackNotFound:
            raise
        except Exception as e:
            logger.exception(f"Error updating feedback status: {str(e)}")
            raise FeedbackUpdateError()

    async def delete_feedback(self, feedback_id: str, user_id: str) -> bool:
        try:
            existing = await self.repository.find_by_id(feedback_id)
            if not existing:
                raise FeedbackNotFound()

            # Ensure user owns the feedback
            if existing.get("user_id") != user_id:
                # We could raise a 403 Forbidden, but raising NotFound is safer to prevent enumeration
                raise FeedbackNotFound()

            success = await self.repository.delete_by_id_and_user_id(
                feedback_id, user_id
            )
            if not success:
                raise Exception("Failed to delete feedback")

            return True
        except FeedbackNotFound:
            raise
        except Exception as e:
            logger.exception(f"Error deleting feedback: {str(e)}")
            raise FeedbackDeleteError()
