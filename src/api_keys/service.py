import secrets

from src.api_keys.constants import Info
from src.api_keys.exceptions import (
    APIKeyCreationError,
    APIKeyDeletionError,
    APIKeyNotFoundError,
    InvalidAPIKeyError,
)
from src.api_keys.repository import ApiKeyRepository
from src.api_keys.schemas import APIKeysResponse, CreateAPIKey
from src.config import Settings
from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger
from src.utils import hash_token

logger = create_logger("api_keys_service", __name__)


class ApiKeyService:
    def __init__(
        self,
        repository: ApiKeyRepository,
        background_tasks: BackgroundTaskRunner,
        config: Settings,
    ):
        self.repository = repository
        self.background_tasks = background_tasks
        self.config = config

    async def create_api_key(self, user_id: str) -> APIKeysResponse:
        try:
            api_key = f"{self.config.api_key_prefix}{secrets.token_urlsafe(32)}"
            hash_key = hash_token(api_key)
            data = CreateAPIKey(userId=user_id, hashKey=hash_key)

            await self.check_and_delete_api_key(user_id)
            await self.repository.insert_api_key(data)

            return APIKeysResponse(
                apiKey=api_key, detail=Info.API_KEY_CREATED + " " + Info.API_KEY_WARNING
            )
        except Exception as e:
            logger.exception(f"Error creating API key for user {user_id}: {str(e)}")
            raise APIKeyCreationError()

    async def check_and_delete_api_key(self, user_id: str) -> bool:
        current_api_key = await self.repository.find_user_api_key(user_id)
        if current_api_key:
            deleted = await self.repository.delete_user_api_key(user_id)
            return deleted.deleted_count == 1

        return False

    async def delete_api_key(self, user_id: str) -> APIKeysResponse:
        try:
            if await self.check_and_delete_api_key(user_id):
                return APIKeysResponse(apiKey="", detail=Info.API_KEY_DELETED)

            raise APIKeyNotFoundError()
        except APIKeyNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error deleting API key for user {user_id}: {str(e)}")
            raise APIKeyDeletionError()

    async def update_last_used_api_key(self, user_id: str) -> bool:
        updated = await self.repository.update_last_used_api_key(user_id)
        return updated.modified_count == 1

    async def validate_api_key(self, api_key: str) -> dict:
        hash_key = hash_token(api_key)

        try:
            user = await self.repository.find_user_by_hash_key(hash_key)
            if not user:
                raise InvalidAPIKeyError()

            self.background_tasks.add_task(
                self.update_last_used_api_key, user["userId"]
            )

            return user
        except InvalidAPIKeyError:
            raise
        except Exception as e:
            logger.exception(f"Error validating API key: {str(e)}")
            raise InvalidAPIKeyError()
