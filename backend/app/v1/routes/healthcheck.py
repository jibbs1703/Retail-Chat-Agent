"""Retail Product Agent Backend Healthcheck Routes Module."""

from app.v1.core.configurations import get_settings
from app.v1.models.healthcheck import HealthCheckResponse
from app.v1.services.healthcheck import (
    check_postgres_health,
    check_qdrant_health,
    check_redis_health,
)
from fastapi import APIRouter

router = APIRouter()
settings = get_settings()


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
    postgres_status, postgres_response_time, postgres_details = await check_postgres_health()
    redis_status, redis_response_time, redis_details = await check_redis_health()
    qdrant_status, qdrant_response_time, qdrant_details = await check_qdrant_health()

    health_check = {
        "status": "Running",
        "version": settings.application_version,
        "postgres": {
            "status": postgres_status,
            "response_time": postgres_response_time,
            "details": postgres_details,
        },
        "redis": {
            "status": redis_status,
            "response_time": redis_response_time,
            "details": redis_details,
        },
        "qdrant": {
            "status": qdrant_status,
            "response_time": qdrant_response_time,
            "details": qdrant_details,
        },
    }
    return HealthCheckResponse(**health_check)
