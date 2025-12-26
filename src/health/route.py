from fastapi import APIRouter, Depends, Response, status

from src.dependencies import get_health_service
from src.health.constants import HealthStatus
from src.health.schemas import HealthCheckResponse
from src.health.service import HealthService

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    response: Response,
    service: HealthService = Depends(get_health_service),
):
    health_status = await service.check_health()

    if health_status.status == HealthStatus.ERROR:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        response.status_code = status.HTTP_200_OK

    return health_status
