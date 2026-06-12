"""White-label branding: admin configuration + public theme endpoint."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.branding import get_branding

router = APIRouter()
public_router = APIRouter()

HEX_PATTERN = r"^#[0-9a-fA-F]{6}$"


class BrandingUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_dark_url: Optional[str] = None
    logo_light_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=HEX_PATTERN)
    accent_color: Optional[str] = Field(None, pattern=HEX_PATTERN)
    custom_domain: Optional[str] = None


class BrandingResponse(BaseModel):
    id: UUID
    company_name: str
    logo_dark_url: Optional[str]
    logo_light_url: Optional[str]
    primary_color: str
    accent_color: str
    custom_domain: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=BrandingResponse)
async def get_branding_config(db: AsyncSession = Depends(get_db)):
    """Admin configuration dashboard read."""
    return await get_branding(db)


@router.patch("/", response_model=BrandingResponse)
async def update_branding_config(
    data: BrandingUpdate, db: AsyncSession = Depends(get_db)
):
    """Change the entire platform identity live — no redeploy."""
    branding = await get_branding(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(branding, field, value)
    branding.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(branding)
    return branding


@public_router.get("/branding")
async def public_branding(db: AsyncSession = Depends(get_db)):
    """Unauthenticated theme bootstrap (login screens, embeds)."""
    branding = await get_branding(db)
    return JSONResponse(
        content={
            "company_name": branding.company_name,
            "logo_dark_url": branding.logo_dark_url,
            "logo_light_url": branding.logo_light_url,
            "primary_color": branding.primary_color,
            "accent_color": branding.accent_color,
            "custom_domain": branding.custom_domain,
        },
        headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "max-age=60"},
    )
