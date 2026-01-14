"""Retail Product Agent Backend Healthcheck Routes Module."""

from typing import Any

from fastapi import APIRouter
from httpx import AsyncClient, HTTPError, TimeoutException

from app.v1.core.configurations import get_settings

router = APIRouter()


async def get_qdrant_collections() -> list[str]:
    """Retrieve Qdrant collections."""
    settings = get_settings()
    qdrant_collections = []
    try:
        async with AsyncClient() as http_client:
            response = await http_client.get(
                f"{settings.qdrant_url}/collections", timeout=5.0
            )
            if response.status_code == 200:
                collections_data = response.json()
                for collection in collections_data.get("collections", []):
                    qdrant_collections.append(collection.get("name"))
        return qdrant_collections
    except (HTTPError, TimeoutException):
        qdrant_collections = [{"error": "Could not connect to Qdrant"}]
    return qdrant_collections


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Check the health of services needed for the application.

    Args:
        None

    Returns:
        Dictionary containing health status information.
    """
    return {
        "Backend Status": "Running",
        "Qdrant Collections": await get_qdrant_collections(),
    }
