"""Agency-level management of sub-accounts (workspaces).

These routes are intentionally NOT tenant-scoped: they are how the client
discovers which workspaces exist before selecting one.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tenancy import Agency, SubAccount, IndustryType

router = APIRouter()

# ============ SCHEMAS ============

class SubAccountCreate(BaseModel):
    name: str
    industry_type: IndustryType = IndustryType.OTHER
    logo_url: Optional[str] = None
    custom_domain: Optional[str] = None
    timezone: str = "America/Denver"

class SubAccountUpdate(BaseModel):
    name: Optional[str] = None
    industry_type: Optional[IndustryType] = None
    logo_url: Optional[str] = None
    custom_domain: Optional[str] = None
    timezone: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    from_name: Optional[str] = None
    reply_to_email: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None

class SubAccountResponse(BaseModel):
    id: UUID
    agency_id: UUID
    name: str
    industry_type: IndustryType
    logo_url: Optional[str]
    custom_domain: Optional[str]
    timezone: str
    quiet_hours_start: str
    quiet_hours_end: str
    from_name: Optional[str]
    reply_to_email: Optional[str]
    twilio_phone_number: Optional[str]
    owner_email: Optional[str]
    owner_phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ============ ROUTES ============

async def _default_agency(db: AsyncSession) -> Agency:
    result = await db.execute(select(Agency).order_by(Agency.created_at).limit(1))
    agency = result.scalar_one_or_none()
    if agency is None:
        raise HTTPException(status_code=500, detail="No agency configured")
    return agency

@router.get("/", response_model=List[SubAccountResponse])
async def list_sub_accounts(db: AsyncSession = Depends(get_db)):
    """List all sub-accounts (workspaces) in the agency."""
    result = await db.execute(select(SubAccount).order_by(SubAccount.created_at))
    return result.scalars().all()

@router.post("/", response_model=SubAccountResponse, status_code=201)
async def create_sub_account(data: SubAccountCreate, db: AsyncSession = Depends(get_db)):
    """Create a new isolated workspace."""
    agency = await _default_agency(db)
    sub_account = SubAccount(agency_id=agency.id, **data.model_dump())
    db.add(sub_account)
    await db.flush()
    await db.refresh(sub_account)
    return sub_account

@router.get("/{sub_account_id}", response_model=SubAccountResponse)
async def get_sub_account(sub_account_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubAccount).where(SubAccount.id == sub_account_id))
    sub_account = result.scalar_one_or_none()
    if sub_account is None:
        raise HTTPException(status_code=404, detail="Sub-account not found")
    return sub_account

@router.patch("/{sub_account_id}", response_model=SubAccountResponse)
async def update_sub_account(
    sub_account_id: UUID, data: SubAccountUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SubAccount).where(SubAccount.id == sub_account_id))
    sub_account = result.scalar_one_or_none()
    if sub_account is None:
        raise HTTPException(status_code=404, detail="Sub-account not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sub_account, field, value)
    sub_account.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(sub_account)
    return sub_account

@router.delete("/{sub_account_id}")
async def delete_sub_account(sub_account_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubAccount).where(SubAccount.id == sub_account_id))
    sub_account = result.scalar_one_or_none()
    if sub_account is None:
        raise HTTPException(status_code=404, detail="Sub-account not found")
    await db.delete(sub_account)
    return {"deleted": True, "id": str(sub_account_id)}
