# ==============================================================================
# Build Stage for enum-worker
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy workspace dependency definitions
COPY pyproject.toml uv.lock ./
COPY packages/schema ./packages/schema
COPY apps/worker ./apps/worker
COPY apps/api ./apps/api

# Install dependencies for enum-worker (excludes API web dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --package enum-worker

# ==============================================================================
# Production Runtime Stage
# ==============================================================================
FROM python:3.14-slim-bookworm AS runtime

WORKDIR /app

# Create non-root system user
RUN useradd -u 1001 -U -d /app -s /bin/false appuser

# Copy uv binary for runtime use
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy virtual environment and application code from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/packages/schema /app/packages/schema
COPY --from=builder --chown=appuser:appuser /app/apps/worker /app/apps/worker



ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/apps/worker/src:/app/packages/schema/src" \
    UV_CACHE_DIR="/tmp/.uv-cache"


USER appuser

CMD ["celery", "-A", "enum_worker.celery_app", "worker", "--loglevel=info"]
