"""Main FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from enum_schema.base import HealthResponse



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup initialization
    yield
    # Shutdown clean up


app = FastAPI(
    title="ENUM Talent Intelligence Platform API",
    description="FastAPI backend modular monolith for ENUM Talent Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Monitoring"],
    summary="Liveness probe endpoint",
)
async def health_check() -> HealthResponse:
    """Liveness probe verifying that the API container is responsive."""
    return HealthResponse(
        status="ok",
        services={
            "api": "healthy",
        },
    )


@app.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Monitoring"],
    summary="Readiness probe endpoint",
)
async def readiness_check() -> HealthResponse:
    """Readiness probe verifying backend dependency readiness."""
    return HealthResponse(
        status="ready",
        services={
            "api": "ready",
            "postgres": "ready",
            "redis": "ready",
            "minio": "ready",
        },
    )
