"""A2P/SMS compliance guard.

The ComplianceRegistry tracks opt-outs per phone number per sub-account.
Inbound STOP/UNSUBSCRIBE/QUIT keywords flip `has_opted_out` instantly, and
the pre-flight interceptor (`assert_can_message`) is consulted before ANY
outbound SMS or email — manual sends and workflow steps alike.
"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact
from app.models.automations import ComplianceRegistry


class ComplianceBlockedError(Exception):
    """Raised when an outbound message is blocked by compliance rules."""


def normalize_phone(phone: str) -> str:
    """Last 10 digits — good enough to match NANP numbers across formats."""
    return "".join(ch for ch in (phone or "") if ch.isdigit())[-10:]


async def is_opted_out(
    db: AsyncSession, sub_account_id: uuid.UUID, phone: str
) -> bool:
    normalized = normalize_phone(phone)
    if not normalized:
        return False
    result = await db.execute(
        select(ComplianceRegistry).where(
            ComplianceRegistry.sub_account_id == sub_account_id,
            ComplianceRegistry.phone_number == normalized,
        )
    )
    entry = result.scalar_one_or_none()
    return bool(entry and entry.has_opted_out)


async def record_opt_out(
    db: AsyncSession, sub_account_id: uuid.UUID, phone: str, source: str = "manual"
) -> None:
    """Instantly flip the registry status for this number to opted-out, and
    mirror the flag onto matching contacts."""
    normalized = normalize_phone(phone)
    if not normalized:
        return

    result = await db.execute(
        select(ComplianceRegistry).where(
            ComplianceRegistry.sub_account_id == sub_account_id,
            ComplianceRegistry.phone_number == normalized,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        entry = ComplianceRegistry(
            sub_account_id=sub_account_id, phone_number=normalized
        )
        db.add(entry)
    entry.has_opted_out = True
    entry.opted_out_at = datetime.utcnow()
    entry.opt_out_source = source
    entry.updated_at = datetime.utcnow()

    result = await db.execute(
        select(Contact).where(
            Contact.sub_account_id == sub_account_id,
            Contact.phone.ilike(f"%{normalized}"),
        )
    )
    for contact in result.scalars().all():
        contact.do_not_disturb = True
        contact.status = "unsubscribed"
        contact.sms_consent = False

    await db.flush()


async def record_opt_in(
    db: AsyncSession, sub_account_id: uuid.UUID, phone: str
) -> None:
    """Clear the opted-out flag (START / resubscribe keywords)."""
    normalized = normalize_phone(phone)
    if not normalized:
        return

    result = await db.execute(
        select(ComplianceRegistry).where(
            ComplianceRegistry.sub_account_id == sub_account_id,
            ComplianceRegistry.phone_number == normalized,
        )
    )
    entry = result.scalar_one_or_none()
    if entry:
        entry.has_opted_out = False
        entry.updated_at = datetime.utcnow()

    result = await db.execute(
        select(Contact).where(
            Contact.sub_account_id == sub_account_id,
            Contact.phone.ilike(f"%{normalized}"),
        )
    )
    for contact in result.scalars().all():
        contact.do_not_disturb = False
        contact.status = "active"
        contact.sms_consent = True

    await db.flush()


async def assert_can_message(
    db: AsyncSession, sub_account_id: uuid.UUID, contact: Contact, channel: str
) -> None:
    """Pre-flight interceptor. Raises ComplianceBlockedError if this
    destination must not be messaged."""
    if contact.do_not_disturb:
        raise ComplianceBlockedError("Contact is marked do-not-disturb")

    status = getattr(contact.status, "value", contact.status)
    if status == "unsubscribed":
        raise ComplianceBlockedError("Contact has unsubscribed")

    if channel == "sms":
        if not contact.phone:
            raise ComplianceBlockedError("Contact has no phone number")
        if await is_opted_out(db, sub_account_id, contact.phone):
            raise ComplianceBlockedError(
                "Phone number is in the opt-out registry (A2P compliance)"
            )
    elif channel == "email" and not contact.email:
        raise ComplianceBlockedError("Contact has no email address")
