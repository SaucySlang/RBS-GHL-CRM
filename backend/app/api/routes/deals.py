from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.tenancy import require_sub_account
from app.models import Contact, Deal, DealStage, SubAccount
from app.services.pipeline_events import pipeline_manager, deal_event

router = APIRouter()

# ============ SCHEMAS ============

class DealCreate(BaseModel):
    title: str
    value: Decimal = Decimal("0")
    contact_id: Optional[UUID] = None
    stage: DealStage = DealStage.NEW_LEAD
    position: float = 0

class DealUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[Decimal] = None
    contact_id: Optional[UUID] = None
    stage: Optional[DealStage] = None
    lost_reason: Optional[str] = None
    position: Optional[float] = None

class DealMove(BaseModel):
    stage: DealStage
    position: float = 0
    lost_reason: Optional[str] = None

class DealResponse(BaseModel):
    id: UUID
    sub_account_id: UUID
    contact_id: Optional[UUID]
    title: str
    value: Decimal
    stage: DealStage
    lost_reason: Optional[str]
    position: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============ ROUTES (strictly sub-account scoped) ============

@router.get("/", response_model=List[DealResponse])
async def list_deals(
    stage: Optional[DealStage] = None,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """List deals for the active sub-account's pipeline."""
    query = select(Deal).where(Deal.sub_account_id == sub_account.id)
    if stage:
        query = query.where(Deal.stage == stage)
    query = query.order_by(Deal.position.asc(), Deal.created_at.asc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=DealResponse, status_code=201)
async def create_deal(
    data: DealCreate,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Create a deal in the active sub-account."""
    if data.contact_id:
        result = await db.execute(
            select(Contact).where(
                Contact.id == data.contact_id,
                Contact.sub_account_id == sub_account.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Contact not found")

    deal = Deal(sub_account_id=sub_account.id, **data.model_dump())
    db.add(deal)
    await db.flush()
    await db.refresh(deal)
    await pipeline_manager.broadcast(sub_account.id, deal_event("deal_created", deal))
    return deal

@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    deal = await _get_scoped_deal(db, deal_id, sub_account.id)
    return deal

@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: UUID,
    data: DealUpdate,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    deal = await _get_scoped_deal(db, deal_id, sub_account.id)

    update_data = data.model_dump(exclude_unset=True)
    _validate_lost_reason(update_data.get("stage", deal.stage), update_data, deal)

    for field, value in update_data.items():
        setattr(deal, field, value)
    deal.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(deal)
    await pipeline_manager.broadcast(sub_account.id, deal_event("deal_updated", deal))
    return deal

@router.post("/{deal_id}/move", response_model=DealResponse)
async def move_deal(
    deal_id: UUID,
    data: DealMove,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Move a deal to another pipeline stage (Kanban drag & drop).

    Moving into LOST requires a lost_reason.
    """
    deal = await _get_scoped_deal(db, deal_id, sub_account.id)

    payload = data.model_dump()
    _validate_lost_reason(data.stage, payload, deal)

    deal.stage = data.stage
    deal.position = data.position
    if data.stage == DealStage.LOST:
        deal.lost_reason = data.lost_reason
    elif deal.lost_reason and data.stage != DealStage.LOST:
        deal.lost_reason = None  # revived deals shed their lost reason
    deal.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(deal)
    await pipeline_manager.broadcast(sub_account.id, deal_event("deal_moved", deal))
    return deal

@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    deal = await _get_scoped_deal(db, deal_id, sub_account.id)
    await db.delete(deal)
    await pipeline_manager.broadcast(
        sub_account.id, {"type": "deal_deleted", "deal": {"id": str(deal_id)}}
    )
    return {"deleted": True, "id": str(deal_id)}

# ============ HELPERS ============

async def _get_scoped_deal(db: AsyncSession, deal_id: UUID, sub_account_id: UUID) -> Deal:
    result = await db.execute(
        select(Deal).where(Deal.id == deal_id, Deal.sub_account_id == sub_account_id)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

def _validate_lost_reason(stage, payload: dict, deal: Deal) -> None:
    if stage == DealStage.LOST and not (payload.get("lost_reason") or deal.lost_reason):
        raise HTTPException(
            status_code=422,
            detail="A lost_reason is required when moving a deal to Lost",
        )
