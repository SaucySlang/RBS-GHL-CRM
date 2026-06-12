"""Branding resolution: single BrandingConfig row backed by .env defaults."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.branding import BrandingConfig


async def get_branding(db: AsyncSession) -> BrandingConfig:
    """Fetch the active branding row, creating it from .env defaults on
    first access."""
    result = await db.execute(select(BrandingConfig).limit(1))
    branding = result.scalar_one_or_none()
    if branding is None:
        branding = BrandingConfig(
            company_name=settings.BRAND_COMPANY_NAME,
            logo_dark_url=settings.BRAND_LOGO_DARK_URL,
            logo_light_url=settings.BRAND_LOGO_LIGHT_URL,
            primary_color=settings.BRAND_PRIMARY_COLOR,
            accent_color=settings.BRAND_ACCENT_COLOR,
            custom_domain=settings.BRAND_CUSTOM_DOMAIN,
        )
        db.add(branding)
        await db.flush()
    return branding
