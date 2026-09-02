# ==============================================================================
# Build Stage for enum-api
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy workspace dependency definitions
COPY pyproject.toml uv.lock ./
COPY packages/schema ./packages/schema
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

# Install dependencies for enum-api
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --package enum-api

# ==============================================================================
# Production Runtime Stage
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Create non-root system user
RUN useradd -u 1001 -U -d /app -s /bin/false appuser

# Copy uv binary for runtime use
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy virtual environment and application code from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/packages/schema /app/packages/schema
COPY --from=builder --chown=appuser:appuser /app/apps/api /app/apps/api



ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/apps/api/src:/app/packages/schema/src" \
    UV_CACHE_DIR="/tmp/.uv-cache"


USER appuser

EXPOSE 8000

CMD ["uvicorn", "enum_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
