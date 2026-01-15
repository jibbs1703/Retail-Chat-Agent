"""Retail Product Agent Backend Healthcheck Models Module."""

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    backend_status: str
    qdrant_collections: list[str | dict[str, str]]
