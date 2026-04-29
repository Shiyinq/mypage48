from fastapi import APIRouter, Depends

from src.dependencies import get_current_user, get_llm_service, require_csrf_protection
from src.llm.schemas import AnalysisResult, AnalyzeImageRequest
from src.llm.service import LLMService

router = APIRouter()


@router.post("/analyze-ticket", response_model=AnalysisResult)
async def analyze_ticket(
    request: AnalyzeImageRequest,
    current_user=Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
    _=Depends(require_csrf_protection),
):
    """
    Analyze a ticket image and extract details using Gemini.
    Requires authentication.
    """
    return await service.analyze_ticket_image(request)
