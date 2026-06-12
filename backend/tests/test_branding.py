"""White-label branding configuration."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import async_engine, Base
from app.main import app
from app.services.seed import seed_default_tenants

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture()
async def client():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_tenants()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await async_engine.dispose()


async def test_branding_seeded_from_env_and_editable(client):
    # First read seeds the row from .env defaults
    resp = await client.get("/api/v1/branding/")
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "LeadStack"
    assert resp.json()["primary_color"] == "#8B5CF6"

    # Admin dashboard can re-skin the platform live
    resp = await client.patch(
        "/api/v1/branding/",
        json={
            "company_name": "Zenith CRM",
            "primary_color": "#22D3EE",
            "custom_domain": "crm.zenith.example",
        },
    )
    assert resp.status_code == 200

    # Public theme bootstrap reflects it instantly
    resp = await client.get("/api/v1/public/branding")
    body = resp.json()
    assert body["company_name"] == "Zenith CRM"
    assert body["primary_color"] == "#22D3EE"

    # Color validation
    resp = await client.patch("/api/v1/branding/", json={"primary_color": "purple"})
    assert resp.status_code == 422
