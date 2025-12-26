from typing import Optional
from pydantic import BaseModel, Field


class AnalyzeImageRequest(BaseModel):
    image: str = Field(description="Base64 encoded image string")


class AnalysisResult(BaseModel):
    title: str
    date: str = Field(description="YYYY-MM-DD")
    time: str
    gate_open: Optional[str] = None
    day: str
    section: str
    number: str
    price: float
    ticket_id: str
