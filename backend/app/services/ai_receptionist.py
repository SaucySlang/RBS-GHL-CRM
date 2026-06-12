"""AI receptionist: isolated per-sub-account persona answering web chat and
inbound SMS, autonomously extracting name + phone and promoting the
conversation into a concrete Contact in that workspace's pipeline."""
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, Conversation, SubAccount
from app.models.ai import AIReceptionistConfig, ChatSession
from app.services.ai_provider import AIProvider, AIProviderError

logger = logging.getLogger(__name__)

EXTRACT_PATTERN = re.compile(r"<extract>(.*?)</extract>", re.DOTALL)
PHONE_PATTERN = re.compile(r"\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
NAME_PATTERN = re.compile(
    r"\b(?:my name is|i am|i'm|this is)\s+([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?)",
    re.IGNORECASE,
)

FALLBACK_REPLY = (
    "Thanks for reaching out! A member of our team will get back to you "
    "very shortly. If it's urgent, please leave your name and phone number."
)


def build_system_prompt(sub_account: SubAccount, config: AIReceptionistConfig) -> str:
    """The persona is strictly scoped to one business sub-account."""
    return f"""You are the virtual receptionist for "{sub_account.name}".

Business context (cleaned from the company's own materials):
{config.prompt_context or 'No additional context provided yet.'}

Rules:
- You ONLY represent {sub_account.name}. Never mention other businesses.
- Be warm, concise, and useful. Two or three sentences per reply.
- Your quiet goal: learn the visitor's NAME and PHONE NUMBER naturally in
  conversation — never as an interrogation. Ask at a natural moment.
- The moment you have learned the visitor's name and/or phone number,
  append a machine block to the very end of your reply, exactly like:
  <extract>{{"name": "Jane Doe", "phone": "+15551234567"}}</extract>
  Include only the fields you actually learned. The block is stripped
  before the visitor sees your message.
- Never invent contact details. Never promise pricing you don't know."""


async def get_config(
    db: AsyncSession, sub_account_id: uuid.UUID
) -> Optional[AIReceptionistConfig]:
    result = await db.execute(
        select(AIReceptionistConfig).where(
            AIReceptionistConfig.sub_account_id == sub_account_id
        )
    )
    return result.scalar_one_or_none()


def parse_extraction(reply: str, user_message: str) -> tuple[str, dict]:
    """Split the agent's reply into (visible_text, extracted fields).

    The LLM's <extract> block is authoritative; deterministic regex over the
    user's own words is the fallback so capture works even when the model
    omits the block (or no provider is reachable)."""
    extracted: dict = {}

    match = EXTRACT_PATTERN.search(reply)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                if data.get("name"):
                    extracted["name"] = str(data["name"]).strip()
                if data.get("phone"):
                    extracted["phone"] = str(data["phone"]).strip()
        except json.JSONDecodeError:
            logger.warning("Unparseable <extract> block from model")
    visible = EXTRACT_PATTERN.sub("", reply).strip()

    if "phone" not in extracted:
        phone_match = PHONE_PATTERN.search(user_message)
        if phone_match:
            extracted["phone"] = phone_match.group(0).strip()
    if "name" not in extracted:
        name_match = NAME_PATTERN.search(user_message)
        if name_match:
            extracted["name"] = name_match.group(1).strip()

    return visible, extracted


async def promote_session_to_contact(
    db: AsyncSession, session: ChatSession, sub_account: SubAccount
) -> Optional[Contact]:
    """Upgrade a chat session into a concrete Contact once name+phone exist.
    (Also exposed as POST /receptionist/sessions/{id}/promote.)"""
    extracted = session.extracted or {}
    if session.contact_id or not (extracted.get("name") and extracted.get("phone")):
        return None

    name_parts = extracted["name"].split(maxsplit=1)
    contact = Contact(
        sub_account_id=sub_account.id,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else None,
        phone=extracted["phone"],
        source="ai_receptionist",
        source_id=str(session.id),
        sms_consent=True,
    )
    db.add(contact)
    await db.flush()
    session.contact_id = contact.id
    session.updated_at = datetime.utcnow()

    # Drop the new lead straight into this workspace's pipeline
    from app.services.workflow_engine import trigger_workflows

    await trigger_workflows(
        db,
        sub_account_id=sub_account.id,
        trigger_type="contact_created",
        contact=contact,
        context={"chat_session_id": str(session.id)},
    )
    logger.info(
        "Chat session %s promoted to contact %s in %s",
        session.id, contact.id, sub_account.name,
    )
    return contact


async def _generate_reply(
    config: AIReceptionistConfig,
    sub_account: SubAccount,
    transcript: list[dict],
) -> str:
    provider = AIProvider(preferred=config.model_provider)
    try:
        return await provider.generate(
            system=build_system_prompt(sub_account, config),
            messages=[
                {"role": m["role"], "content": m["content"]} for m in transcript
            ],
        )
    except AIProviderError:
        logger.warning(
            "No AI provider reachable for sub-account %s; using fallback reply",
            sub_account.id,
        )
        return FALLBACK_REPLY


async def handle_web_chat(
    db: AsyncSession,
    sub_account: SubAccount,
    visitor_key: str,
    user_message: str,
) -> tuple[str, ChatSession]:
    """Web-chat widget ingestion -> AI reply + autonomous lead capture."""
    config = await get_config(db, sub_account.id)
    if config is None or not config.web_chat_enabled:
        return FALLBACK_REPLY, await _get_or_create_session(db, sub_account, visitor_key)

    session = await _get_or_create_session(db, sub_account, visitor_key)
    transcript = list(session.transcript or [])
    transcript.append(
        {"role": "user", "content": user_message, "at": datetime.utcnow().isoformat()}
    )

    raw_reply = await _generate_reply(config, sub_account, transcript)
    visible, extracted = parse_extraction(raw_reply, user_message)

    session.extracted = {**(session.extracted or {}), **extracted}
    transcript.append(
        {"role": "assistant", "content": visible, "at": datetime.utcnow().isoformat()}
    )
    session.transcript = transcript
    session.updated_at = datetime.utcnow()
    await db.flush()

    await promote_session_to_contact(db, session, sub_account)
    return visible, session


async def handle_inbound_sms(
    db: AsyncSession,
    sub_account: SubAccount,
    contact: Contact,
    conversation: Conversation,
    body: str,
) -> Optional[str]:
    """Inbound Twilio SMS routed through the same AI generation service.
    Returns the reply text (sent back as TwiML) or None when AI is off."""
    config = await get_config(db, sub_account.id)
    if config is None or not config.sms_enabled or not conversation.ai_enabled:
        return None

    # Rebuild the transcript from the stored conversation thread
    from app.models import Message

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .limit(30)
    )
    transcript = [
        {
            "role": "user" if m.direction == "inbound" else "assistant",
            "content": m.body,
        }
        for m in result.scalars().all()
    ] or [{"role": "user", "content": body}]

    raw_reply = await _generate_reply(config, sub_account, transcript)
    visible, extracted = parse_extraction(raw_reply, body)

    # SMS already gives us the phone; fold in a learned name
    if extracted.get("name") and not contact.first_name:
        name_parts = extracted["name"].split(maxsplit=1)
        contact.first_name = name_parts[0]
        if len(name_parts) > 1:
            contact.last_name = name_parts[1]
        contact.updated_at = datetime.utcnow()

    # Record the assistant reply in the thread
    reply_message = Message(
        sub_account_id=sub_account.id,
        contact_id=contact.id,
        conversation_id=conversation.id,
        channel="sms",
        direction="outbound",
        status="sent",
        from_address=sub_account.twilio_phone_number,
        to_address=contact.phone,
        body=visible,
        provider="twilio",
        ai_generated=True,
        sent_at=datetime.utcnow(),
    )
    db.add(reply_message)
    conversation.last_message_at = datetime.utcnow()
    conversation.last_message_preview = visible[:255]
    await db.flush()

    return visible


async def _get_or_create_session(
    db: AsyncSession, sub_account: SubAccount, visitor_key: str
) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.sub_account_id == sub_account.id,
            ChatSession.visitor_key == visitor_key,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        session = ChatSession(
            sub_account_id=sub_account.id, visitor_key=visitor_key, transcript=[]
        )
        db.add(session)
        await db.flush()
    return session
