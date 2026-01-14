"""Retail Product Agent Backend Core Configurations Module."""

from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings for the Give-It-A-Summary backend.

    Settings can be loaded from environment variables or .env file.

    """

    load_dotenv()
    application_api_prefix: str = "/api/v1"
    application_description: str = "AI powered multimodal product search backend."
    application_name: str = "Retail Product Agent Backend"
    application_version: str = "1.0.0"
    application_debug_flag: bool = False

    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "http://localhost:6379"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get or create a cached Settings instance.

    Returns:
        Settings: Cached application settings instance.
    """
    return Settings()
