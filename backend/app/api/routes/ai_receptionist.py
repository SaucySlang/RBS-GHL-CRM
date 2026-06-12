"""AI receptionist configuration + multi-channel ingestion routes."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.tenancy import require_sub_account, tenant_context
from app.models import SubAccount
from app.models.ai import AIReceptionistConfig, ChatSession
from app.services.ai_receptionist import (
    get_config, handle_web_chat, promote_session_to_contact,
)
from app.services.html_cleaner import clean_training_input

router = APIRouter()

PUBLIC_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

# ============ SCHEMAS ============

class ConfigUpdate(BaseModel):
    prompt_context: Optional[str] = None
    model_provider: Optional[str] = None
    web_chat_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None

class ConfigResponse(BaseModel):
    id: UUID
    sub_account_id: UUID
    prompt_context: str
    model_provider: str
    web_chat_enabled: bool
    sms_enabled: bool
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainRequest(BaseModel):
    # A homepage URL or raw pasted text/HTML
    source: str
    append: bool = False

class SessionResponse(BaseModel):
    id: UUID
    visitor_key: str
    transcript: List[dict]
    extracted: dict
    contact_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WebChatMessage(BaseModel):
    visitor_key: str
    message: str

# ============ CONFIG (tenant-scoped) ============

@router.get("/config", response_model=ConfigResponse)
async def get_receptionist_config(
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    config = await get_config(db, sub_account.id)
    if config is None:
        config = AIReceptionistConfig(sub_account_id=sub_account.id)
        db.add(config)
        await db.flush()
        await db.refresh(config)
    return config

@router.patch("/config", response_model=ConfigResponse)
async def update_receptionist_config(
    data: ConfigUpdate,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    config = await get_config(db, sub_account.id)
    if config is None:
        config = AIReceptionistConfig(sub_account_id=sub_account.id)
        db.add(config)
        await db.flush()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    config.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(config)
    return config

@router.post("/config/train", response_model=ConfigResponse)
async def train_from_source(
    data: TrainRequest,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Paste a homepage URL or raw text: HTML tags, scripts and CSS are
    stripped and only clean markdown enters the prompt context."""
    try:
        cleaned = await clean_training_input(data.source)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not ingest source: {exc}")
    if not cleaned:
        raise HTTPException(status_code=422, detail="Source produced no usable text")

    config = await get_config(db, sub_account.id)
    if config is None:
        config = AIReceptionistConfig(sub_account_id=sub_account.id)
        db.add(config)
        await db.flush()

    config.prompt_context = (
        f"{config.prompt_context}\n\n{cleaned}".strip() if data.append else cleaned
    )
    config.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(config)
    return config

# ============ SESSIONS (tenant-scoped) ============

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.sub_account_id == sub_account.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(100)
    )
    return result.scalars().all()

@router.post("/sessions/{session_id}/promote")
async def promote_session(
    session_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Internal route: upgrade a chat session into a concrete Contact."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.sub_account_id == sub_account.id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    contact = await promote_session_to_contact(db, session, sub_account)
    if contact is None and session.contact_id is None:
        raise HTTPException(
            status_code=422,
            detail="Session has not yet captured both a name and phone number",
        )
    return {
        "promoted": True,
        "contact_id": str(session.contact_id or contact.id),
    }

# ============ PUBLIC WEB-CHAT WIDGET (unauthenticated) ============

public_router = APIRouter()

@public_router.options("/chat/{sub_account_id}", include_in_schema=False)
async def chat_preflight(sub_account_id: UUID):
    return JSONResponse(content=None, status_code=204, headers=PUBLIC_CORS_HEADERS)

@public_router.post("/chat/{sub_account_id}")
async def web_chat(
    sub_account_id: UUID,
    data: WebChatMessage,
    db: AsyncSession = Depends(get_db),
):
    """Web-chat widget ingestion. The sub-account id in the URL selects
    which isolated persona answers."""
    result = await db.execute(
        select(SubAccount).where(SubAccount.id == sub_account_id)
    )
    sub_account = result.scalar_one_or_none()
    if sub_account is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    with tenant_context(sub_account.id):
        reply, session = await handle_web_chat(
            db, sub_account, data.visitor_key, data.message
        )
        await db.commit()

    return JSONResponse(
        content={
            "reply": reply,
            "session_id": str(session.id),
            "contact_created": session.contact_id is not None,
        },
        headers=PUBLIC_CORS_HEADERS,
    )
