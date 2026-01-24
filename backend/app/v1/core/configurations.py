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
    application_description: str = "AI powered multimodal product search backend."
    application_device: str = "cpu"
    application_name: str = "Retail Product Agent Backend"
    application_version: str = "1.0.0"
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID")
    aws_region: str = os.getenv("AWS_REGION")
    aws_s3_bucket_name: str = os.getenv("AWS_S3_BUCKET_NAME")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    blip_model_name: str = os.getenv("BLIP_MODEL_NAME")
    clip_model_name: str = os.getenv("CLIP_MODEL_NAME")
    max_image_size: int = int(os.getenv("MAX_IMAGE_SIZE"))
    postgres_database: str = os.getenv("POSTGRES_DATABASE")
    postgres_host: str = os.getenv("POSTGRES_HOST")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD")
    postgres_port: int = int(os.getenv("POSTGRES_PORT"))
    postgres_user: str = os.getenv("POSTGRES_USER")
    product_default_categories: list[str] = ["shoes", "bodysuits", "jackets"]
    product_default_pages_per_category: int = 3
    product_default_products_per_page: int = 60
    product_default_concurrent_requests: int = 5
    qdrant_url: str = os.getenv("QDRANT_URL")
    redis_url: str = os.getenv("REDIS_URL")
    rerank_model_name: str = os.getenv("RERANK_MODEL_NAME")
    supported_image_extensions: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    supported_image_formats: set[str] = {"JPEG", "PNG", "GIF", "WEBP", "BMP"}


@lru_cache
def get_settings() -> ApplicationSettings:
    """Get or create a cached ApplicationSettings instance.

    Returns:
        ApplicationSettings: Cached application settings instance.
    """
    return ApplicationSettings()
