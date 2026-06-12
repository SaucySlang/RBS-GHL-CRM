"""Deal pipeline: stage moves, lost-reason enforcement, tenant scoping."""
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


async def _workspace(client):
    resp = await client.get("/api/v1/sub-accounts/")
    return resp.json()[0]["id"]


async def test_deal_lifecycle_and_lost_reason_required(client):
    sub = await _workspace(client)
    headers = {"X-SubAccount-ID": sub}

    resp = await client.post(
        "/api/v1/deals/",
        json={"title": "Studio booking — EP production", "value": "4500"},
        headers=headers,
    )
    assert resp.status_code == 201
    deal = resp.json()
    assert deal["stage"] == "new_lead"

    # Normal stage move works
    resp = await client.post(
        f"/api/v1/deals/{deal['id']}/move",
        json={"stage": "qualified", "position": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["stage"] == "qualified"

    # Moving to Lost without a reason is rejected
    resp = await client.post(
        f"/api/v1/deals/{deal['id']}/move",
        json={"stage": "lost", "position": 1},
        headers=headers,
    )
    assert resp.status_code == 422

    # With a reason it succeeds
    resp = await client.post(
        f"/api/v1/deals/{deal['id']}/move",
        json={"stage": "lost", "position": 1, "lost_reason": "Budget cut"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["lost_reason"] == "Budget cut"

    # Reviving the deal clears the lost reason
    resp = await client.post(
        f"/api/v1/deals/{deal['id']}/move",
        json={"stage": "contacted", "position": 2},
        headers=headers,
    )
    assert resp.json()["lost_reason"] is None


async def test_deals_isolated_between_workspaces(client):
    resp = await client.get("/api/v1/sub-accounts/")
    sub_a, sub_b = resp.json()[0]["id"], resp.json()[1]["id"]

    resp = await client.post(
        "/api/v1/deals/",
        json={"title": "Listing: 42 Wallaby Way", "value": "12000"},
        headers={"X-SubAccount-ID": sub_a},
    )
    deal_id = resp.json()["id"]

    resp = await client.get("/api/v1/deals/", headers={"X-SubAccount-ID": sub_b})
    assert resp.json() == []

    resp = await client.get(
        f"/api/v1/deals/{deal_id}", headers={"X-SubAccount-ID": sub_b}
    )
    assert resp.status_code == 404
