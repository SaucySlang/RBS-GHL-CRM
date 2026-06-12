from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.tenancy import require_sub_account
from app.models import Message, Contact, SubAccount

router = APIRouter()

# Schemas
class MessageSend(BaseModel):
    contact_id: UUID
    channel: str = "sms"
    body: str

class MessageResponse(BaseModel):
    id: UUID
    contact_id: UUID
    channel: str
    direction: str
    status: str
    body: str
    from_address: Optional[str]
    to_address: Optional[str]
    ai_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[MessageResponse])
async def list_messages(
    contact_id: Optional[UUID] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """List messages in the active sub-account."""
    query = select(Message).where(Message.sub_account_id == sub_account.id)
    if contact_id:
        query = query.where(Message.contact_id == contact_id)
    if channel:
        query = query.where(Message.channel == channel)
    query = query.order_by(Message.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/send", response_model=MessageResponse)
async def send_message(
    data: MessageSend,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to a contact (compliance-guarded)."""
    result = await db.execute(
        select(Contact).where(
            Contact.id == data.contact_id, Contact.sub_account_id == sub_account.id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    from app.services.messaging import send_to_contact

    message = await send_to_contact(
        db=db,
        sub_account=sub_account,
        contact=contact,
        channel=data.channel,
        body=data.body,
    )
    return message

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Get a message by ID."""
    result = await db.execute(
        select(Message).where(
            Message.id == message_id, Message.sub_account_id == sub_account.id
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
