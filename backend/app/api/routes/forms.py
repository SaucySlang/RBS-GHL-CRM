"""Authenticated form-builder CRUD (tenant-scoped)."""
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.tenancy import require_sub_account
from app.models import SubAccount
from app.models.forms import Form, DEFAULT_FORM_FIELDS, DEFAULT_FORM_CONFIG

router = APIRouter()

# ============ SCHEMAS ============

class FormCreate(BaseModel):
    name: str
    fields_json: Optional[List[dict]] = None
    configurations_json: Optional[dict] = None

class FormUpdate(BaseModel):
    name: Optional[str] = None
    fields_json: Optional[List[dict]] = None
    configurations_json: Optional[dict] = None
    is_published: Optional[bool] = None

class FormResponse(BaseModel):
    id: UUID
    sub_account_id: UUID
    name: str
    fields_json: List[dict]
    configurations_json: dict
    is_published: bool
    submission_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmbedResponse(BaseModel):
    form_id: UUID
    embed_url: str
    snippet: str

# ============ ROUTES ============

@router.get("/", response_model=List[FormResponse])
async def list_forms(
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form)
        .where(Form.sub_account_id == sub_account.id)
        .order_by(Form.created_at.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=FormResponse, status_code=201)
async def create_form(
    data: FormCreate,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    form = Form(
        sub_account_id=sub_account.id,
        name=data.name,
        fields_json=data.fields_json or list(DEFAULT_FORM_FIELDS),
        configurations_json=data.configurations_json or dict(DEFAULT_FORM_CONFIG),
    )
    db.add(form)
    await db.flush()
    await db.refresh(form)
    return form

@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    return await _get_scoped_form(db, form_id, sub_account.id)

@router.patch("/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: UUID,
    data: FormUpdate,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_scoped_form(db, form_id, sub_account.id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(form, field, value)
    form.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(form)
    return form

@router.delete("/{form_id}")
async def delete_form(
    form_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_scoped_form(db, form_id, sub_account.id)
    await db.delete(form)
    return {"deleted": True, "id": str(form_id)}

@router.get("/{form_id}/embed", response_model=EmbedResponse)
async def get_embed_code(
    form_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Raw HTML iframe snippet for the 'Copy Embed Code' button."""
    form = await _get_scoped_form(db, form_id, sub_account.id)
    embed_url = f"{settings.PUBLIC_BASE_URL}{settings.API_PREFIX}/public/forms/{form.id}/render"
    snippet = (
        f'<iframe src="{embed_url}" width="100%" height="560" '
        f'style="border:none;border-radius:12px;overflow:hidden" '
        f'title="{form.name}" loading="lazy"></iframe>'
    )
    return EmbedResponse(form_id=form.id, embed_url=embed_url, snippet=snippet)

async def _get_scoped_form(db: AsyncSession, form_id: UUID, sub_account_id: UUID) -> Form:
    result = await db.execute(
        select(Form).where(Form.id == form_id, Form.sub_account_id == sub_account_id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form
