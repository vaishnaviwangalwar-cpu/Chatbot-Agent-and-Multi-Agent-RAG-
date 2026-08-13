import logging
from google.genai import types

from app.config import settings
from app.genai_client import get_genai_client

logger = logging.getLogger(__name__)


class ParsingAgent:
    """Specialist agent for layout-aware text extraction from PDFs, images, and text files."""

    def parse_file(self, file_bytes: bytes, mime_type: str) -> str:
        """Extracts structured text from an uploaded file using Gemini multimodal vision."""
        # Plain text — decode directly without an LLM call
        if mime_type == "text/plain":
            return file_bytes.decode("utf-8")

        logger.info(f"Invoking Parsing Agent (Gemini) for MIME type: {mime_type}")
        response = get_genai_client().models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                "Extract all readable text, instructions, rules, and tables from this document into clean, structured markdown text. Return only the extracted content."
            ]
        )
        return response.text or ""


parsing_agent = ParsingAgent()
