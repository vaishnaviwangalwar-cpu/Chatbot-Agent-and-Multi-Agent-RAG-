from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    embedding_model: str = "gemini-embedding-001"
    chroma_path: str = "./chroma_db"
    top_k: int = 3
    host: str = "0.0.0.0"
    port: int = 8001


settings = Settings()
