from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.tenancy import require_sub_account
from app.models import Conversation, Message, SubAccount

router = APIRouter()

class ConversationResponse(BaseModel):
    id: UUID
    contact_id: UUID
    channel: str
    status: str
    ai_enabled: bool
    last_message_at: Optional[datetime]
    last_message_preview: Optional[str]
    unread_count: int
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    status: Optional[str] = "open",
    limit: int = 50,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """List conversations in the active sub-account."""
    query = select(Conversation).where(Conversation.sub_account_id == sub_account.id)
    if status:
        query = query.where(Conversation.status == status)
    query = query.order_by(Conversation.last_message_at.desc().nulls_last()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.sub_account_id == sub_account.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = 100,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Get messages in a conversation."""
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sub_account_id == sub_account.id,
        )
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    return result.scalars().all()

@router.patch("/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: UUID,
    status: str,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Update conversation status (open/closed/snoozed)."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.sub_account_id == sub_account.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.status = status
    conv.updated_at = datetime.utcnow()
    return {"id": str(conversation_id), "status": status}

@router.patch("/{conversation_id}/ai")
async def toggle_ai(
    conversation_id: UUID,
    enabled: bool,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable AI for a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.sub_account_id == sub_account.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.ai_enabled = enabled
    return {"id": str(conversation_id), "ai_enabled": enabled}
