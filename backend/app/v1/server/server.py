"""Retail Product Agent Backend Server Module."""


from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def run_application() -> FastAPI:
    """Initialize and configure FastAPI application with middleware and routes.

    Creates FastAPI instance with configuration from settings, registers CORS
    middleware for frontend communication, includes all API routes with
    version prefix, and sets up lifespan context for database
    initialization. Returns fully configured application ready for ASGI
    server.

    Returns:
        FastAPI: Configured application instance with middleware
    """

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = run_application()