from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables or .env file.
    Follows 12-factor app principles for environment-driven configuration.
    """

    # Gemini API Key (Google AI Studio Key)
    gemini_api_key: str = ""

    # Model ID to use - defaulting to Gemini 3.1+ tier model
    gemini_model: str = "gemini-3.1-flash-lite"

    # Hyperparameters & Generation Control
    max_output_tokens: int = 1024
    temperature: float = 0.7
    top_p: Optional[float] = None  # None uses Gemini model default
    top_k: Optional[int] = None    # None uses Gemini model default
    thinking_level: str = "MINIMAL"  # Supported: MINIMAL, LOW, MEDIUM, HIGH

    # Server settings
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000

    # Conversation Memory settings
    max_session_turns: int = 10  # Caps token usage by keeping last N turns

    # Pydantic Settings configuration to automatically read from .env
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Instantiate a global singleton settings object
settings = Settings()
