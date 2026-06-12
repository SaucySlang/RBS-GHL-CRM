"""AI receptionist: context stripping, extraction, lead promotion, isolation."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import async_engine, Base
from app.main import app
from app.services.html_cleaner import strip_html_to_markdown
from app.services.ai_receptionist import parse_extraction
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


def test_html_stripping_keeps_only_clean_text():
    html = """
    <html><head><title>x</title><style>body { color: red }</style></head>
    <body>
      <script>alert('tracking')</script>
      <h1>Acme Studios</h1>
      <p>We produce <b>chart-ready</b> records.</p>
      <ul><li>Mixing</li><li>Mastering</li></ul>
      <a href="https://acme.example/book">Book now</a>
    </body></html>
    """
    out = strip_html_to_markdown(html)
    assert "# Acme Studios" in out
    assert "chart-ready" in out
    assert "- Mixing" in out
    assert "[Book now](https://acme.example/book)" in out
    assert "alert" not in out
    assert "color: red" not in out
    assert "<" not in out


def test_extraction_block_and_regex_fallback():
    visible, extracted = parse_extraction(
        'Great, I\'ll pass that on!<extract>{"name": "Jane Doe", "phone": "+15551234567"}</extract>',
        user_message="whatever",
    )
    assert visible == "Great, I'll pass that on!"
    assert extracted == {"name": "Jane Doe", "phone": "+15551234567"}

    # No block from the model -> deterministic fallback from the user's words
    _, extracted = parse_extraction(
        "Thanks!", user_message="Hi, my name is Sarah Connor, call me at (555) 123-4567"
    )
    assert extracted["name"] == "Sarah Connor"
    assert "555" in extracted["phone"]


async def test_web_chat_promotes_session_to_contact(client):
    resp = await client.get("/api/v1/sub-accounts/")
    sub = resp.json()[0]["id"]
    headers = {"X-SubAccount-ID": sub}

    # Configure the persona for this workspace
    resp = await client.patch(
        "/api/v1/receptionist/config",
        json={"prompt_context": "We sell beats.", "model_provider": "anthropic"},
        headers=headers,
    )
    assert resp.status_code == 200

    # Visitor chats and reveals name + phone (no AI keys configured in test
    # env -> provider chain falls back to the polite default, but the
    # deterministic extractor still captures the lead)
    resp = await client.post(
        f"/api/v1/public/chat/{sub}",
        json={
            "visitor_key": "visitor-1",
            "message": "Hey! My name is Sarah Connor, you can reach me at 555-123-4567",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"]
    assert body["contact_created"] is True

    # The contact landed in this workspace's pipeline
    resp = await client.get("/api/v1/contacts/", headers=headers)
    contacts = resp.json()
    assert any(
        c["first_name"] == "Sarah" and c["source"] == "ai_receptionist"
        for c in contacts
    )

    # ...and is invisible from any other workspace
    resp = await client.get("/api/v1/sub-accounts/")
    other = resp.json()[1]["id"]
    resp = await client.get("/api/v1/contacts/", headers={"X-SubAccount-ID": other})
    assert resp.json() == []


async def test_session_listing_and_transcript(client):
    resp = await client.get("/api/v1/sub-accounts/")
    sub = resp.json()[0]["id"]
    headers = {"X-SubAccount-ID": sub}

    await client.patch("/api/v1/receptionist/config", json={}, headers=headers)
    await client.post(
        f"/api/v1/public/chat/{sub}",
        json={"visitor_key": "v-2", "message": "What are your hours?"},
    )

    resp = await client.get("/api/v1/receptionist/sessions", headers=headers)
    sessions = resp.json()
    assert len(sessions) == 1
    transcript = sessions[0]["transcript"]
    assert transcript[0]["role"] == "user"
    assert transcript[1]["role"] == "assistant"
