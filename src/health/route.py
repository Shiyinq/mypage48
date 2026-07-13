from fastapi import APIRouter, Depends, Response, status

from src.auth.schemas import UserCurrent
from src.dependencies import get_health_service, require_admin
from src.health.constants import HealthStatus
from src.health.schemas import HealthCheckResponse, RecorderHeartbeatRequest
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


@router.post("/health/recorder", status_code=status.HTTP_200_OK)
async def record_recorder_heartbeat(
    request: RecorderHeartbeatRequest,
    service: HealthService = Depends(get_health_service),
    current_user: "UserCurrent" = Depends(require_admin),
):
    """
    Endpoint for the recorder script to send its heartbeat.
    Requires Admin privileges (or Admin API Key).
    """
    await service.record_recorder_heartbeat(
        mode=request.mode,
        bot_token=request.bot_token,
        chat_id=request.chat_id,
    )
    return {"status": "ok"}
