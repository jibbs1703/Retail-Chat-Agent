"""Retail Product Agent Backend Healthcheck Routes Module."""

from fastapi import APIRouter
from httpx import AsyncClient, HTTPError, TimeoutException

from app.v1.core.configurations import get_settings
from app.v1.models.healthcheck import HealthCheckResponse

router = APIRouter()


async def get_qdrant_collections() -> list[str]:
    """Retrieve Qdrant collections."""
    settings = get_settings()
    qdrant_collections = []
    try:
        async with AsyncClient() as http_client:
            response = await http_client.get(f"{settings.qdrant_url}/collections", timeout=5.0)
            if response.status_code == 200:
                collections_data = response.json()
                for collection in collections_data.get("collections", []):
                    qdrant_collections.append(collection.get("name"))
        return qdrant_collections
    except (HTTPError, TimeoutException):
        qdrant_collections = [{"error": "Could not connect to Qdrant"}]
    return qdrant_collections


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health of the backend and its dependencies.",
)
async def health_check() -> HealthCheckResponse:
    """
    Check the health of services needed for the application.

    Args:
        None

    Returns:
        Dictionary containing health status information.
    """
    health_check = {
        "backend_status": "Running",
        "qdrant_collections": await get_qdrant_collections(),
    }
    return HealthCheckResponse(**health_check)
