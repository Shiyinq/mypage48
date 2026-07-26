from typing import List

from fastapi import APIRouter, Depends

from src.concerts.schemas import ConcertResponse, CreateConcert, UpdateConcert
from src.concerts.service import ConcertsService
from src.dependencies import (
    get_concerts_service,
    require_admin,
    require_csrf_protection,
)

router = APIRouter()


@router.post("/", status_code=201, response_model=ConcertResponse)
async def create_concert(
    data: CreateConcert,
    current_user=Depends(require_admin),
    _=Depends(require_csrf_protection),
    service: ConcertsService = Depends(get_concerts_service),
):
    return await service.create_concert(data)


@router.get("/", response_model=List[ConcertResponse])
async def get_all_concerts(
    service: ConcertsService = Depends(get_concerts_service),
):
    return await service.get_all_concerts()


@router.get("/{concert_id}", response_model=ConcertResponse)
async def get_concert(
    concert_id: str,
    service: ConcertsService = Depends(get_concerts_service),
):
    return await service.get_concert(concert_id)


@router.put("/{concert_id}", response_model=ConcertResponse)
async def update_concert(
    concert_id: str,
    data: UpdateConcert,
    current_user=Depends(require_admin),
    _=Depends(require_csrf_protection),
    service: ConcertsService = Depends(get_concerts_service),
):
    return await service.update_concert(concert_id, data)


@router.delete("/{concert_id}", status_code=200)
async def delete_concert(
    concert_id: str,
    current_user=Depends(require_admin),
    _=Depends(require_csrf_protection),
    service: ConcertsService = Depends(get_concerts_service),
):
    return await service.delete_concert(concert_id)
