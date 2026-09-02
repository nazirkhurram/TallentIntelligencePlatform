import pytest
from httpx import ASGITransport, AsyncClient

from enum_api.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Verify that the API health probe returns HTTP 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_check() -> None:
    """Verify that the API readiness probe returns HTTP 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
