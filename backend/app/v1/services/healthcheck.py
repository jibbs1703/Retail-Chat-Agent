"""Retail Product Agent Backend Healthcheck Services Module."""

import psycopg2
import redis.asyncio as redis
from app.v1.core.configurations import get_settings
from fastapi import APIRouter
from httpx import AsyncClient, HTTPError, TimeoutException
from psycopg2 import sql

router = APIRouter()
settings = get_settings()


async def get_redis_keys(pattern: str = "*", limit: int = 100) -> list[str] | list[dict]:
    """Retrieve Redis Keys."""
    redis_keys = []

    if not settings.redis_url:
        return [{"error": "Redis URL not configured"}]

    try:
        client = redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=5.0)

        async with client:
            cursor, keys = await client.scan(cursor=0, match=pattern, count=limit)
            redis_keys = keys

        return redis_keys if redis_keys else [{"info": "No keys found in Redis Database"}]

    except (HTTPError, TimeoutException):
        return [{"error": "Could not connect to Redis"}]


async def get_qdrant_collections() -> list[str] | list[dict]:
    """Retrieve Qdrant collections."""
    qdrant_collections = []

    if not settings.qdrant_url:
        return [{"error": "Qdrant URL not configured"}]

    try:
        async with AsyncClient() as http_client:
            response = await http_client.get(f"{settings.qdrant_url}/collections", timeout=5.0)
            if response.status_code == 200:
                collections_data = response.json()
                for collection in collections_data.get("result", {}).get("collections", []):
                    qdrant_collections.append(collection.get("name"))
        return qdrant_collections
    except (HTTPError, TimeoutException):
        qdrant_collections = [{"error": "Could not connect to Qdrant"}]
    return (
        qdrant_collections
        if qdrant_collections
        else [{"info": "No collections found in Qdrant Vector Database"}]
    )


async def get_postgres_tables() -> list[str] | list[dict]:
    """Retrieve PostgreSQL table names from the retail_catalog database."""
    postgres_tables = []

    if not any(
        [
            settings.postgres_database,
            settings.postgres_host,
            settings.postgres_password,
            settings.postgres_port,
            settings.postgres_user,
        ]
    ):
        return [{"error": "PostgreSQL URL not configured"}]

    try:
        database_url = (
            f"postgresql://{settings.postgres_user}:"
            f"{settings.postgres_password}@"
            f"{settings.postgres_host}:"
            f"{settings.postgres_port}/"
            f"{settings.postgres_database}"
        )

        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        cursor.execute(
            sql.SQL(
                """
                SELECT tablename FROM pg_tables 
                WHERE schemaname = %s
                """
            ),
            ("public",),
        )

        tables = cursor.fetchall()
        postgres_tables = [table[0] for table in tables]

        cursor.close()
        conn.close()

        return postgres_tables if postgres_tables else [{"info": "No tables in public schema"}]

    except psycopg2.OperationalError:
        return [{"error": "Could not connect to PostgreSQL"}]
    except (HTTPError, ConnectionError) as e:
        return [{"error": f"PostgreSQL error: {str(e)}"}]
