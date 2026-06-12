"""Workspace isolation: data must never leak across sub-accounts."""
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


async def _two_workspaces(client):
    resp = await client.get("/api/v1/sub-accounts/")
    assert resp.status_code == 200
    subs = resp.json()
    assert len(subs) >= 2
    return subs[0]["id"], subs[1]["id"]


async def test_header_required(client):
    resp = await client.get("/api/v1/contacts/")
    assert resp.status_code == 422  # missing X-SubAccount-ID


async def test_invalid_header_rejected(client):
    resp = await client.get("/api/v1/contacts/", headers={"X-SubAccount-ID": "nope"})
    assert resp.status_code == 400


async def test_contacts_isolated_between_sub_accounts(client):
    sub_a, sub_b = await _two_workspaces(client)

    resp = await client.post(
        "/api/v1/contacts/",
        json={"first_name": "Alice", "phone": "+15550000001"},
        headers={"X-SubAccount-ID": sub_a},
    )
    assert resp.status_code == 201
    alice_id = resp.json()["id"]

    resp = await client.post(
        "/api/v1/contacts/",
        json={"first_name": "Bob", "phone": "+15550000002"},
        headers={"X-SubAccount-ID": sub_b},
    )
    assert resp.status_code == 201
    bob_id = resp.json()["id"]

    # Workspace A sees only Alice
    resp = await client.get("/api/v1/contacts/", headers={"X-SubAccount-ID": sub_a})
    names = [c["first_name"] for c in resp.json()]
    assert names == ["Alice"]

    # Workspace B sees only Bob
    resp = await client.get("/api/v1/contacts/", headers={"X-SubAccount-ID": sub_b})
    names = [c["first_name"] for c in resp.json()]
    assert names == ["Bob"]

    # Cross-tenant direct fetch is a 404, not a leak
    resp = await client.get(
        f"/api/v1/contacts/{bob_id}", headers={"X-SubAccount-ID": sub_a}
    )
    assert resp.status_code == 404

    # Cross-tenant update/delete blocked too
    resp = await client.patch(
        f"/api/v1/contacts/{alice_id}",
        json={"first_name": "Hacked"},
        headers={"X-SubAccount-ID": sub_b},
    )
    assert resp.status_code == 404
    resp = await client.delete(
        f"/api/v1/contacts/{alice_id}", headers={"X-SubAccount-ID": sub_b}
    )
    assert resp.status_code == 404
