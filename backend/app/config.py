"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the TruthLens API."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TruthLens"
    environment: str = "development"
    serpapi_api_key: str | None = None
    llm_provider: str = "not_configured"
    llm_model: str = "not_configured"


settings = Settings()
