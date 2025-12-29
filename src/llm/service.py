import google.generativeai as genai
import json
from src.config import Settings
from src.logging_config import create_logger
from src.llm.repository import LLMRepository
from src.llm.schemas import AnalyzeImageRequest, AnalysisResult
from src.llm.exceptions import ImageAnalysisError

logger = create_logger("llm_service", __name__)


class LLMService:
    def __init__(
        self,
        repository: LLMRepository,
        config: Settings,
    ):
        self.repository = repository
        self.config = config
        
        # Configure Gemini
        genai.configure(api_key=self.config.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def analyze_ticket_image(self, request: AnalyzeImageRequest) -> AnalysisResult:
        try:
            # Clean base64 if needed
            base64_image = request.image
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]

            prompt = """
            Analyze this JKT48 theater ticket image. 
            Extract the following details:
            1. Title of the show.
            2. Date (Convert to YYYY-MM-DD format).
            3. Time of the show (e.g., 14:00 or 19:00).
            4. Gate Open Time (usually labeled 'OPEN GATE', e.g., 18:30).
            5. Day of the week.
            6. Seat Section/Row (The letter part, e.g., "G").
            7. Seat Number (The number part, e.g., "3" from "G-3").
            8. Price (Numeric only).
            9. Ticket Number (The large ID number).
            """

            # Prepare content for Gemini
            # The SDK supports passing image data as a dict with 'mime_type' and 'data'
            image_part = {
                "mime_type": "image/jpeg",
                "data": base64_image
            }

            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "date": {"type": "STRING", "description": "YYYY-MM-DD"},
                        "time": {"type": "STRING"},
                        "gate_open": {"type": "STRING"},
                        "day": {"type": "STRING"},
                        "section": {"type": "STRING", "description": "Row letter"},
                        "number": {"type": "STRING", "description": "Seat number only"},
                        "price": {"type": "NUMBER"},
                        "ticket_id": {"type": "STRING"},
                    },
                    "required": ["title", "date", "section", "number", "price"]
                }
            )

            response = await self.model.generate_content_async(
                contents=[image_part, prompt],
                generation_config=generation_config
            )
            
            json_text = response.text
            if not json_text:
                raise ImageAnalysisError("Empty response from Gemini")
            
            data = json.loads(json_text)
            return AnalysisResult(**data)

        except Exception as e:
            logger.exception(f"Error analyzing image: {str(e)}")
            raise ImageAnalysisError()
