import os
import logging
from google import genai

from app.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def get_genai_client() -> genai.Client:
    """Returns a shared, lazily-initialized Google GenAI client for the entire app."""
    global _client
    if _client is None:
        api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured! Please add your Google AI Studio API key to the .env file."
            )
        _client = genai.Client(api_key=api_key)
        logger.info("Google GenAI client initialized.")
    return _client
