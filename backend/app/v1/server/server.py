"""Retail Product Agent Backend Server Module."""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.v1.core.configurations import get_settings
from app.v1.routes import api_router


def run_application() -> FastAPI:
    """
    Initialize and configure FastAPI application with middleware and routes.

    Returns:
        FastAPI: Configured application instance with middleware
    """
    settings = get_settings()
    app = FastAPI(
        title=settings.application_name,
        version=settings.application_version,
        debug=settings.application_debug_flag,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.application_api_prefix)

    return app


app = run_application()
