from fastapi import APIRouter, Depends, status

from src.auth.schemas import UserCurrent
from src.dependencies import (
    get_current_user,
    get_sorters_service,
    require_csrf_protection,
)
from src.sorter.exceptions import SorterNotFoundError, SorterSaveError
from src.sorter.http_exceptions import SorterNotFound, SorterSaveFailed
from src.sorter.schemas import (
    SorterCreateRequest,
    SorterPaginationResponse,
    SorterResponse,
    SorterUpdateRequest,
)
from src.sorter.service import SortersService

router = APIRouter()


@router.post("", response_model=SorterResponse, status_code=status.HTTP_201_CREATED)
async def create_sorter(
    data: SorterCreateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    _=Depends(require_csrf_protection),
    service: SortersService = Depends(get_sorters_service),
):
    try:
        return await service.save_sorter(user_id=current_user.userId, data=data)
    except SorterSaveError:
        raise SorterSaveFailed()


@router.get("", response_model=SorterPaginationResponse)
async def get_sorters(
    page: int = 1,
    limit: int = 15,
    current_user: UserCurrent = Depends(get_current_user),
    service: SortersService = Depends(get_sorters_service),
):
    return await service.get_sorters(
        user_id=current_user.userId, page=page, limit=limit
    )


@router.get("/{sorter_id}", response_model=SorterResponse)
async def get_sorter(
    sorter_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: SortersService = Depends(get_sorters_service),
):
    try:
        return await service.get_sorter(
            sorter_id=sorter_id, user_id=current_user.userId
        )
    except SorterNotFoundError:
        raise SorterNotFound()


@router.patch("/{sorter_id}", response_model=SorterResponse)
async def update_sorter(
    sorter_id: str,
    data: SorterUpdateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    _=Depends(require_csrf_protection),
    service: SortersService = Depends(get_sorters_service),
):
    try:
        return await service.update_sorter(
            sorter_id=sorter_id, user_id=current_user.userId, data=data
        )
    except SorterNotFoundError:
        raise SorterNotFound()


@router.delete("/{sorter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sorter(
    sorter_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    _=Depends(require_csrf_protection),
    service: SortersService = Depends(get_sorters_service),
):
    try:
        await service.delete_sorter(sorter_id=sorter_id, user_id=current_user.userId)
    except SorterNotFoundError:
        raise SorterNotFound()
