from fastapi import APIRouter, Depends
from src.dependencies import get_llm_service, get_current_user
from src.llm.service import LLMService
from src.llm.schemas import AnalyzeImageRequest, AnalysisResult

router = APIRouter()


@router.post("/analyze-ticket", response_model=AnalysisResult)
async def analyze_ticket(
    request: AnalyzeImageRequest,
    current_user=Depends(get_current_user),
    service: LLMService = Depends(get_llm_service),
):
    """
    Analyze a ticket image and extract details using Gemini.
    Requires authentication.
    """
    return await service.analyze_ticket_image(request)
