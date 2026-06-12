import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID


class BrandingConfig(Base):
    """Platform-wide white-label identity (single row, seeded from .env).

    Everything visual — names, logos, colors, domains — flows from here at
    runtime; nothing is hardcoded in the frontend."""
    __tablename__ = "branding_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_name = Column(String(255), nullable=False, default="LeadStack")
    logo_dark_url = Column(String(1024))   # shown on dark surfaces
    logo_light_url = Column(String(1024))  # shown on light surfaces (emails)
    primary_color = Column(String(7), nullable=False, default="#8B5CF6")
    accent_color = Column(String(7), nullable=False, default="#C084FC")
    custom_domain = Column(String(255))

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
