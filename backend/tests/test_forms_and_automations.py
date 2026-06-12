"""Form capture engine + automation engine integration tests."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import async_engine, AsyncSessionLocal, Base
from app.main import app
from app.models.automations import ExecutionState, WorkflowExecutionLog
from app.services.interpolation import render_merge_tags
from app.services.seed import seed_default_tenants
from app.services.workflow_engine import process_due_steps

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


async def _workspace(client, index=0):
    resp = await client.get("/api/v1/sub-accounts/")
    return resp.json()[index]["id"]


async def _published_form(client, headers):
    resp = await client.post("/api/v1/forms/", json={"name": "Contact us"}, headers=headers)
    assert resp.status_code == 201
    form = resp.json()
    resp = await client.patch(
        f"/api/v1/forms/{form['id']}", json={"is_published": True}, headers=headers
    )
    return resp.json()


def test_merge_tag_interpolation():
    class FakeContact:
        first_name, last_name = "Ada", "Lovelace"
        email, phone, source = "ada@example.com", "+15551234567", "form"

    class FakeSub:
        name, industry_type = "AI Consulting", "ai_consulting"
        from_name = reply_to_email = twilio_phone_number = custom_domain = None

    out = render_merge_tags(
        "Hi {{contact.first_name}}, welcome to {{ sub_account.name }}! {{bad.tag}}",
        contact=FakeContact(), sub_account=FakeSub(),
    )
    assert out == "Hi Ada, welcome to AI Consulting! "


async def test_form_render_is_embeddable(client):
    sub = await _workspace(client)
    headers = {"X-SubAccount-ID": sub}
    form = await _published_form(client, headers)

    resp = await client.get(f"/api/v1/public/forms/{form['id']}/render")
    assert resp.status_code == 200
    # Framing must be explicitly allowed for external landing pages
    assert resp.headers["content-security-policy"] == "frame-ancestors *"
    assert "x-frame-options" not in resp.headers
    assert resp.headers["access-control-allow-origin"] == "*"
    assert "lead-form" in resp.text

    # Embed snippet exposes the iframe code
    resp = await client.get(f"/api/v1/forms/{form['id']}/embed", headers=headers)
    assert "<iframe" in resp.json()["snippet"]


async def test_submission_creates_contact_and_triggers_speed_to_lead(client):
    sub = await _workspace(client)
    headers = {"X-SubAccount-ID": sub}
    form = await _published_form(client, headers)

    resp = await client.post(
        f"/api/v1/public/forms/{form['id']}/submit",
        json={
            "first_name": "Jamie",
            "email": "jamie@example.com",
            "phone": "+15557770001",
            "message": "Interested in a beat pack",
        },
    )
    assert resp.status_code == 200, resp.text
    contact_id = resp.json()["contact_id"]

    # Contact landed in the right workspace
    resp = await client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["source"] == "form"

    # Required-field enforcement from the builder config
    resp = await client.post(
        f"/api/v1/public/forms/{form['id']}/submit", json={"email": "no-name@x.com"}
    )
    assert resp.status_code == 422

    # The seeded Speed-to-Lead chain enqueued its first step
    async with AsyncSessionLocal() as db:
        logs = (
            (await db.execute(
                select(WorkflowExecutionLog).execution_options(skip_tenant_scope=True)
            )).scalars().all()
        )
        assert len(logs) == 1
        assert logs[0].state == ExecutionState.PENDING

        # Run the engine: SMS -> Email -> Wait scheduled
        await process_due_steps(db)   # sms
        await process_due_steps(db)   # email
        await process_due_steps(db)   # wait -> schedules owner notify at +60s
        await db.commit()

        logs = (
            (await db.execute(
                select(WorkflowExecutionLog)
                .order_by(WorkflowExecutionLog.created_at)
                .execution_options(skip_tenant_scope=True)
            )).scalars().all()
        )
        states = [log.state for log in logs]
        assert states[:3] == [
            ExecutionState.COMPLETED,  # immediate SMS
            ExecutionState.COMPLETED,  # immediate email
            ExecutionState.COMPLETED,  # wait node
        ]
        assert states[3] == ExecutionState.PENDING  # owner notify in 60s


async def test_stop_keyword_blocks_future_sends(client):
    sub = await _workspace(client)
    headers = {"X-SubAccount-ID": sub}
    form = await _published_form(client, headers)

    # Inbound STOP from Twilio flips the registry instantly
    resp = await client.post(
        "/api/v1/webhooks/twilio/sms",
        data={
            "From": "+15559990000",
            "To": "+15551112222",
            "Body": "STOP",
            "MessageSid": "SM123",
        },
    )
    assert resp.status_code == 200
    assert "unsubscribed" in resp.text.lower()

    # The same number submits a form -> workflow SMS must be skipped
    resp = await client.post(
        f"/api/v1/public/forms/{form['id']}/submit",
        json={"first_name": "Optout", "email": "o@example.com", "phone": "+1 (555) 999-0000"},
    )
    assert resp.status_code == 200

    async with AsyncSessionLocal() as db:
        await process_due_steps(db)
        await db.commit()
        logs = (
            (await db.execute(
                select(WorkflowExecutionLog)
                .order_by(WorkflowExecutionLog.created_at)
                .execution_options(skip_tenant_scope=True)
            )).scalars().all()
        )
        assert logs[0].state == ExecutionState.SKIPPED_COMPLIANCE
        # Execution aborted: no further steps were scheduled
        assert len(logs) == 1


async def test_quiet_hours_pause_and_reschedule(client):
    sub = await _workspace(client)
    headers = {"X-SubAccount-ID": sub}

    # A window that is never open -> everything pauses
    resp = await client.patch(
        f"/api/v1/sub-accounts/{sub}",
        json={"quiet_hours_start": "12:00", "quiet_hours_end": "12:00", "timezone": "UTC"},
    )
    assert resp.status_code == 200

    form = await _published_form(client, headers)
    resp = await client.post(
        f"/api/v1/public/forms/{form['id']}/submit",
        json={"first_name": "Night", "email": "n@example.com", "phone": "+15553334444"},
    )
    assert resp.status_code == 200

    async with AsyncSessionLocal() as db:
        await process_due_steps(db)
        await db.commit()
        logs = (
            (await db.execute(
                select(WorkflowExecutionLog).execution_options(skip_tenant_scope=True)
            )).scalars().all()
        )
        assert logs[0].state == ExecutionState.PAUSED_QUIET_HOURS
        assert logs[0].scheduled_for > logs[0].created_at
