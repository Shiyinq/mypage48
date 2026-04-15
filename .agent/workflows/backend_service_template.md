---
description: Create a new backend service following the architecture of the api_keys service.
---

This workflow outlines the steps to create a new backend service in `src/`, modeled after the `src/api_keys` service.

**IMPORTANT INSTRUCTION FOR AGENT**:
The code blocks below are **TEMPLATES** using a generic "Item" resource.
When executing this workflow, you MUST:
1.  **Replace** "Item" / "item" with the actual domain entity name requested by the user (e.g., "Notification", "Order", "Product").
2.  **Define** specific fields and logic relevant to that entity instead of using the generic `name` and `id` fields.
3.  **Preserve** the architectural pattern (Repository pattern, Service layer, dependency injection, custom exceptions).

1.  **Create Service Directory**
    Create a new directory for the service: `src/<service_name>/`.
    Inside this directory, create the following empty files:
    - `__init__.py`
    - `constants.py`
    - `exceptions.py`
    - `http_exceptions.py`
    - `schemas.py`
    - `repository.py`
    - `service.py`
    - `route.py`

2.  **Define Constants**
    - file: `src/<service_name>/constants.py`
    
    ```python
    class Info:
        # Define informational messages
        # TODO: Rename/Add messages relevant to your domain
        ITEM_CREATED = "Item created successfully."
        ITEM_DELETED = "Item deleted successfully."


    class ErrorCode:
        # Define error codes for HTTP exceptions
        # TODO: Rename/Add codes relevant to your domain
        ITEM_NOT_FOUND = "Item not found."
        ITEM_CREATE_ERROR = "Failed to create item."


    class DomainErrorCode:
        # Define error codes for Domain exceptions
        # TODO: Rename/Add codes relevant to your domain
        ITEM_NOT_FOUND = "Item not found."
        ITEM_CREATION_FAILED = "Failed to create item."
    ```

3.  **Define Domain Exceptions**
    - file: `src/<service_name>/exceptions.py`
    
    ```python
    from src.<service_name>.constants import DomainErrorCode
    from src.exceptions import DomainException

    # TODO: Create specific exceptions for your domain
    class ItemCreationError(DomainException):
        ERROR_MESSAGE = DomainErrorCode.ITEM_CREATION_FAILED


    class ItemNotFoundError(DomainException):
        ERROR_MESSAGE = DomainErrorCode.ITEM_NOT_FOUND
    ```

4.  **Define HTTP Exceptions**
    - file: `src/<service_name>/http_exceptions.py`

    ```python
    from src.<service_name>.constants import ErrorCode
    from src.http_exceptions import BadRequest, InternalServerError, NotFound

    # TODO: Create specific HTTP exceptions mapping to your domain errors
    class ItemNotFound(NotFound):
        DETAIL = ErrorCode.ITEM_NOT_FOUND


    class ItemCreateError(InternalServerError):
        DETAIL = ErrorCode.ITEM_CREATE_ERROR
    ```

5.  **Implement Schemas**
    - file: `src/<service_name>/schemas.py`

    ```python
    from datetime import datetime
    from typing import Optional
    from pydantic import BaseModel, Field


    class CreateItem(BaseModel):
        # TODO: Define actual fields for creating your resource
        name: str
        createdAt: datetime = Field(default_factory=datetime.now)


    class ItemResponse(BaseModel):
        # TODO: Define actual fields for your resource response
        id: str
        name: str
        detail: Optional[str] = None
    ```

6.  **Implement Repository**
    - file: `src/<service_name>/repository.py`

    ```python
    from typing import Optional, List
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from src.<service_name>.schemas import CreateItem

    class <ServiceName>Repository:
        def __init__(self, db: AsyncIOMotorDatabase):
            self.collection = db["<collection_name>"]

        # TODO: Implement methods relevant to your domain (insert, find, update, delete)
        async def insert_item(self, item_data: CreateItem):
            return await self.collection.insert_one(item_data.model_dump())

        async def find_item_by_id(self, item_id: str) -> Optional[dict]:
            return await self.collection.find_one({"_id": item_id})

        async def delete_item(self, item_id: str):
            return await self.collection.delete_one({"_id": item_id})
    ```

7.  **Implement Service**
    - file: `src/<service_name>/service.py`

    ```python
    from src.config import Settings
    from src.interfaces import BackgroundTaskRunner
    from src.logging_config import create_logger
    from src.<service_name>.repository import <ServiceName>Repository
    from src.<service_name>.schemas import CreateItem, ItemResponse
    from src.<service_name>.constants import Info
    from src.<service_name>.exceptions import ItemCreationError, ItemNotFoundError

    logger = create_logger("<service_name>_service", __name__)

    class <ServiceName>Service:
        def __init__(
            self,
            repository: <ServiceName>Repository,
            background_tasks: BackgroundTaskRunner,
            config: Settings,
        ):
            self.repository = repository
            self.background_tasks = background_tasks
            self.config = config

        # TODO: Implement business logic methods
        async def create_item(self, data: CreateItem) -> ItemResponse:
            try:
                result = await self.repository.insert_item(data)
                return ItemResponse(id=str(result.inserted_id), name=data.name, detail=Info.ITEM_CREATED)
            except Exception as e:
                logger.exception(f"Error creating item: {str(e)}")
                raise ItemCreationError()

        async def get_item(self, item_id: str) -> Optional[ItemResponse]:
            item = await self.repository.find_item_by_id(item_id)
            if not item:
                raise ItemNotFoundError()
            return ItemResponse(**item)
    ```

8.  **Implement Routes**
    - file: `src/<service_name>/route.py`

    ```python
    from fastapi import APIRouter, Depends
    from src.config import config
    # TODO: Add needed dependencies
    from src.dependencies import get_current_user, require_csrf_protection, get_<service_name>_service
    from src.<service_name>.service import <ServiceName>Service
    from src.<service_name>.schemas import ItemResponse, CreateItem

    router = APIRouter()

    # TODO: Define endpoints
    @router.post("/", status_code=201, response_model=ItemResponse)
    async def create_item(
        item_data: CreateItem,
        current_user=Depends(get_current_user),
        _=Depends(require_csrf_protection),
        service: <ServiceName>Service = Depends(get_<service_name>_service),
    ):
        return await service.create_item(item_data)
    ```

9.  **Register Dependencies**
    - file: `src/dependencies.py`
    
    Add the following factory functions:

    ```python
    from src.<service_name>.repository import <ServiceName>Repository
    from src.<service_name>.service import <ServiceName>Service

    def get_<service_name>_repository(db=Depends(get_db)) -> <ServiceName>Repository:
        return <ServiceName>Repository(db)

    def get_<service_name>_service(
        repo: <ServiceName>Repository = Depends(get_<service_name>_repository),
        config: Settings = Depends(get_settings),
    ) -> <ServiceName>Service:
        background_runner = AsyncBackgroundRunner()
        return <ServiceName>Service(repo, background_runner, config)
    ```

10. **Register Router**
    - file: `src/api.py`

    Import and include the router:

    ```python
    from src.<service_name>.route import router as <service_name>_router

    router.include_router(<service_name>_router, prefix="/<service_name>", tags=["<ServiceName>"])
    ```