from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.core.tenancy import tenant_context
from app.models import Message, Contact, Conversation, SubAccount
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

EMPTY_TWIML = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'

OPT_OUT_KEYWORDS = {"stop", "unsubscribe", "quit", "cancel", "end", "stopall", "revoke"}
OPT_IN_KEYWORDS = {"start", "yes", "unstop"}


async def resolve_sub_account_by_number(db: AsyncSession, to_number: str) -> Optional[SubAccount]:
    """Inbound webhooks carry no tenant header; route by the Twilio number
    each sub-account has been assigned."""
    result = await db.execute(
        select(SubAccount).where(SubAccount.twilio_phone_number == to_number)
    )
    sub_account = result.scalars().first()
    if sub_account is None:
        # Fallback: single-tenant setups without a number mapping
        result = await db.execute(
            select(SubAccount).order_by(SubAccount.created_at).limit(1)
        )
        sub_account = result.scalars().first()
    return sub_account


@router.post("/twilio/sms")
async def twilio_sms_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(None),
    NumMedia: int = Form(0),
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming SMS from Twilio: opt-out registry, contact intake,
    conversation threading, and AI receptionist routing."""
    logger.info("Incoming SMS from %s to %s: %s", From, To, Body[:50])

    sub_account = await resolve_sub_account_by_number(db, To)
    if sub_account is None:
        logger.error("No sub-account found for inbound number %s", To)
        return Response(content=EMPTY_TWIML, media_type="application/xml")

    with tenant_context(sub_account.id):
        body_lower = Body.strip().lower()

        # ---- A2P compliance: inbound opt-out / opt-in keywords ----
        from app.services.compliance import record_opt_out, record_opt_in

        if any(keyword in body_lower.split() for keyword in OPT_OUT_KEYWORDS):
            await record_opt_out(db, sub_account.id, From, source="sms_keyword")
            await db.commit()
            return Response(
                content=(
                    '<?xml version="1.0" encoding="UTF-8"?><Response><Message>'
                    "You have been unsubscribed and will receive no further messages. "
                    "Reply START to resubscribe.</Message></Response>"
                ),
                media_type="application/xml",
            )

        # Find or create contact by phone
        phone_tail = "".join(ch for ch in From if ch.isdigit())[-10:]
        result = await db.execute(
            select(Contact).where(
                Contact.sub_account_id == sub_account.id,
                Contact.phone.ilike(f"%{phone_tail}"),
            )
        )
        contact = result.scalars().first()
        if contact is None:
            contact = Contact(
                sub_account_id=sub_account.id,
                phone=From,
                source="sms_inbound",
                sms_consent=True,  # they texted us
            )
            db.add(contact)
            await db.flush()

        if any(keyword in body_lower.split() for keyword in OPT_IN_KEYWORDS):
            await record_opt_in(db, sub_account.id, From)
            contact.do_not_disturb = False
            contact.status = "active"
            contact.sms_consent = True

        # Find or create conversation
        result = await db.execute(
            select(Conversation).where(
                Conversation.sub_account_id == sub_account.id,
                Conversation.contact_id == contact.id,
                Conversation.channel == "sms",
            )
        )
        conversation = result.scalars().first()
        if conversation is None:
            conversation = Conversation(
                sub_account_id=sub_account.id,
                contact_id=contact.id,
                channel="sms",
                status="open",
                ai_enabled=True,
            )
            db.add(conversation)
            await db.flush()

        # Store the inbound message
        message = Message(
            sub_account_id=sub_account.id,
            contact_id=contact.id,
            conversation_id=conversation.id,
            channel="sms",
            direction="inbound",
            status="delivered",
            from_address=From,
            to_address=To,
            body=Body,
            provider="twilio",
            provider_id=MessageSid,
        )
        db.add(message)

        conversation.last_message_at = datetime.utcnow()
        conversation.last_message_preview = Body[:255]
        conversation.unread_count += 1
        contact.last_contacted_at = datetime.utcnow()

        await db.flush()

        # Route through the AI receptionist if enabled for this sub-account
        reply_twiml = EMPTY_TWIML
        from app.services.ai_receptionist import handle_inbound_sms

        ai_reply = await handle_inbound_sms(db, sub_account, contact, conversation, Body)
        if ai_reply:
            from xml.sax.saxutils import escape
            reply_twiml = (
                '<?xml version="1.0" encoding="UTF-8"?><Response><Message>'
                f"{escape(ai_reply)}</Message></Response>"
            )

        await db.commit()

    return Response(content=reply_twiml, media_type="application/xml")


@router.post("/twilio/status")
async def twilio_status_webhook(
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    ErrorCode: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Twilio message status callbacks."""
    logger.info("Message %s status: %s", MessageSid, MessageStatus)

    result = await db.execute(
        select(Message).where(Message.provider_id == MessageSid)
    )
    message = result.scalars().first()

    if message:
        message.provider_status = MessageStatus
        if MessageStatus == "delivered":
            message.status = "delivered"
            message.delivered_at = datetime.utcnow()
        elif MessageStatus == "failed":
            message.status = "failed"

    return {"received": True}


@router.post("/sendgrid/events")
async def sendgrid_events_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle SendGrid email events (opens, clicks, bounces)."""
    events = await request.json()
    for event in events:
        logger.info("Email event: %s for %s", event.get("event"), event.get("email"))
        sg_message_id = (event.get("sg_message_id") or "").split(".")[0]
        if not sg_message_id:
            continue
        result = await db.execute(
            select(Message).where(Message.provider_id == sg_message_id)
        )
        message = result.scalars().first()
        if not message:
            continue
        event_type = event.get("event")
        if event_type == "delivered":
            message.status = "delivered"
            message.delivered_at = datetime.utcnow()
        elif event_type == "open":
            message.status = "opened"
            message.opened_at = datetime.utcnow()
        elif event_type in ("bounce", "dropped"):
            message.status = "failed"
    return {"received": True, "count": len(events)}
