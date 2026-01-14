"""Retail Product Agent Backend Core Configurations Module."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class ApplicationSettings(BaseSettings):
    """
    Application settings for the Give-It-A-Summary backend.

    Settings can be loaded from environment variables or .env file.

    """
    load_dotenv()
    application_api_prefix: str = "/api/v1"
    application_debug_flag: bool = False
    application_device: str = "cpu"
    application_description: str = "AI powered multimodal product search backend."
    application_name: str = "Retail Product Agent Backend"
    application_version: str = "1.0.0"
    qdrant_url: str = os.getenv("qdrant_url")
    redis_url: str = os.getenv("redis_url")


@lru_cache
def get_settings() -> ApplicationSettings:
    """Get or create a cached ApplicationSettings instance.

    Returns:
        ApplicationSettings: Cached application settings instance.
    """
    return ApplicationSettings()
