import base64
import json

from google import genai
from google.genai import types

from src.config import Settings
from src.image_validation import ImageTooLargeError as ImageTooLargeValidationError
from src.image_validation import ImageValidationError
from src.image_validation import (
    InvalidImageTypeError as InvalidImageTypeValidationError,
)
from src.image_validation import validate_base64_image
from src.llm.exceptions import (
    ImageAnalysisError,
    ImageTooLargeError,
    InvalidImageError,
    InvalidImageTypeError,
)
from src.llm.repository import LLMRepository
from src.llm.schemas import AnalysisResult, AnalyzeImageRequest
from src.logging_config import create_logger

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
        self.client = genai.Client(api_key=self.config.gemini_api_key)

    async def analyze_ticket_image(
        self, request: AnalyzeImageRequest
    ) -> AnalysisResult:
        # Validate image before processing
        try:
            validate_base64_image(request.image)
        except ImageTooLargeValidationError:
            raise ImageTooLargeError()
        except InvalidImageTypeValidationError:
            raise InvalidImageTypeError()
        except ImageValidationError:
            raise InvalidImageError()

        try:
            # Clean base64 if needed
            base64_image = request.image
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]

            image_bytes = base64.b64decode(base64_image)

            # Fetch known show titles for context
            show_titles = await self.repository.get_show_titles()
            show_titles_list = "\n".join(f"- {title}" for title in show_titles)

            print(show_titles_list)
            prompt = f"""
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

            IMPORTANT RULES:
            - NEVER include newlines, line breaks, or extra whitespace in any extracted field.
            - For the title, you MUST match it to one of the following known show titles:
            {show_titles_list}

            The text on the ticket may be split across multiple lines or contain apostrophes/special characters.
            Always use the EXACT title from the list above. Do not modify casing, punctuation, or spacing.
            """

            # Prepare content for Gemini
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[image_part, prompt],
                config=types.GenerateContentConfig(
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
                            "number": {
                                "type": "STRING",
                                "description": "Seat number only",
                            },
                            "price": {"type": "NUMBER"},
                            "ticket_id": {"type": "STRING"},
                        },
                        "required": ["title", "date", "section", "number", "price"],
                    },
                ),
            )

            json_text = response.text
            if not json_text:
                raise ImageAnalysisError()

            data = json.loads(json_text)
            return AnalysisResult(**data)

        except (ImageTooLargeError, InvalidImageTypeError, InvalidImageError):
            raise
        except ImageAnalysisError:
            raise
        except Exception as e:
            logger.exception(f"Error analyzing image: {str(e)}")
            raise ImageAnalysisError()
