"""Retail Product Agent Backend Healthcheck Routes Module."""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


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
    }
