"""Outbound messaging: records Message rows and dispatches via providers.

Sender identity (From name / Reply-To / SMS sender) is resolved dynamically
from the active sub-account profile, falling back to platform-level settings.
"""
import logging
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Contact, Conversation, Message, SubAccount
from sqlalchemy import select

logger = logging.getLogger(__name__)


def resolve_sms_sender(sub_account: SubAccount) -> Optional[str]:
    return sub_account.twilio_phone_number or settings.TWILIO_PHONE_NUMBER


def resolve_email_sender(sub_account: SubAccount) -> tuple[Optional[str], str, Optional[str]]:
    """Returns (from_email, from_name, reply_to)."""
    from_email = settings.SENDGRID_FROM_EMAIL
    from_name = sub_account.from_name or sub_account.name
    reply_to = sub_account.reply_to_email
    return from_email, from_name, reply_to


async def _dispatch_sms(to: str, body: str, from_number: Optional[str]) -> tuple[str, Optional[str]]:
    """Send via Twilio REST API. Returns (status, provider_id)."""
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and from_number):
        logger.info("Twilio not configured; SMS to %s recorded as simulated", to)
        return "sent", None

    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    )
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            data={"To": to, "From": from_number, "Body": body},
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
        )
    if resp.status_code >= 400:
        logger.error("Twilio send failed (%s): %s", resp.status_code, resp.text[:500])
        return "failed", None
    return "sent", resp.json().get("sid")


async def _dispatch_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str],
    from_name: str,
    reply_to: Optional[str],
) -> tuple[str, Optional[str]]:
    """Send via SendGrid REST API. Returns (status, provider_id)."""
    if not (settings.SENDGRID_API_KEY and from_email):
        logger.info("SendGrid not configured; email to %s recorded as simulated", to)
        return "sent", None

    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": from_email, "name": from_name},
        "subject": subject or "(no subject)",
        "content": [{"type": "text/plain", "value": body}],
    }
    if reply_to:
        payload["reply_to"] = {"email": reply_to, "name": from_name}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
        )
    if resp.status_code >= 400:
        logger.error("SendGrid send failed (%s): %s", resp.status_code, resp.text[:500])
        return "failed", None
    return "sent", resp.headers.get("X-Message-Id")


async def _get_or_create_conversation(
    db: AsyncSession, sub_account: SubAccount, contact: Contact, channel: str
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.sub_account_id == sub_account.id,
            Conversation.contact_id == contact.id,
            Conversation.channel == channel,
        )
    )
    conversation = result.scalars().first()
    if conversation is None:
        conversation = Conversation(
            sub_account_id=sub_account.id,
            contact_id=contact.id,
            channel=channel,
            status="open",
        )
        db.add(conversation)
        await db.flush()
    return conversation


async def send_to_contact(
    db: AsyncSession,
    sub_account: SubAccount,
    contact: Contact,
    channel: str,
    body: str,
    subject: Optional[str] = None,
    ai_generated: bool = False,
    skip_compliance: bool = False,
) -> Message:
    """Record + dispatch an outbound message with the compliance pre-flight.

    Raises ComplianceBlockedError if the destination has opted out.
    """
    # Pre-flight compliance interceptor (A2P / CAN-SPAM opt-outs)
    if not skip_compliance:
        from app.services.compliance import assert_can_message
        await assert_can_message(db, sub_account.id, contact, channel)

    to_address = contact.phone if channel == "sms" else contact.email
    conversation = await _get_or_create_conversation(db, sub_account, contact, channel)

    if channel == "sms":
        from_number = resolve_sms_sender(sub_account)
        status, provider_id = await _dispatch_sms(to_address, body, from_number)
        from_address, provider = from_number, "twilio"
    else:
        from_email, from_name, reply_to = resolve_email_sender(sub_account)
        # Whitelabel email footer driven by the live branding config
        from app.services.branding import get_branding

        branding = await get_branding(db)
        footer = f"\n\n—\n{from_name}"
        if branding.company_name and branding.company_name != from_name:
            footer += f"\nSent via {branding.company_name}"
        status, provider_id = await _dispatch_email(
            to_address, subject or "", body + footer, from_email, from_name, reply_to
        )
        from_address, provider = from_email, "sendgrid"

    message = Message(
        sub_account_id=sub_account.id,
        contact_id=contact.id,
        conversation_id=conversation.id,
        channel=channel,
        direction="outbound",
        status=status,
        from_address=from_address,
        to_address=to_address,
        subject=subject,
        body=body,
        provider=provider,
        provider_id=provider_id,
        ai_generated=ai_generated,
        sent_at=datetime.utcnow() if status == "sent" else None,
    )
    db.add(message)

    conversation.last_message_at = datetime.utcnow()
    conversation.last_message_preview = body[:255]
    contact.last_contacted_at = datetime.utcnow()

    await db.flush()
    await db.refresh(message)
    return message
