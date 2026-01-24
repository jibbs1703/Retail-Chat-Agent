"""Retail Product Agent Backend Healthcheck Services Module."""

import httpx
import redis.asyncio as redis
from app.v1.core.configurations import get_settings
from httpx import HTTPError

settings = get_settings()


async def check_redis_health(url: str = settings.redis_url) -> tuple[str, float, str]:
    try:
        response = redis.from_url(url, socket_timeout=2.0)
        await response.ping()
        await response.aclose()
        return "Available", 0.0, "Healthy"
    except HTTPError as e:
        return "error", 0.0, str(e)


async def check_qdrant_health(url: str = settings.qdrant_url) -> tuple[str, float, str]:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{url}/collections")
            response.raise_for_status()
            return "Available", response.json().get("time", 0) * 1000, "Healthy"
    except HTTPError as e:
        return "error", 0.0, str(e)


async def check_postgres_health() -> tuple[str, float, str]:
    return "Available", 0.0, "Healthy"
