"""Multi-tenant hierarchy: Agency -> SubAccount -> Member.

Every core CRM table mixes in `TenantMixin`, which adds a mandatory
`sub_account_id` foreign key. Row-level scoping is enforced globally in
`app.core.tenancy` so data can never leak between sub-accounts.
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Table,
    UniqueConstraint, Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declared_attr, declarative_mixin
from app.core.database import Base


class IndustryType(str, enum.Enum):
    REAL_ESTATE = "real_estate"
    MUSIC_PRODUCTION = "music_production"
    ECOMMERCE = "ecommerce"
    AI_CONSULTING = "ai_consulting"
    OTHER = "other"


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Agency(Base):
    """Top-level tenant. Owns sub-accounts (one per business entity)."""
    __tablename__ = "agencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    settings = Column(JSONB, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sub_accounts = relationship(
        "SubAccount", back_populates="agency", cascade="all, delete-orphan"
    )
    members = relationship(
        "Member", back_populates="agency", cascade="all, delete-orphan"
    )


# Members can be granted access to specific sub-accounts.
member_sub_accounts = Table(
    "member_sub_accounts",
    Base.metadata,
    Column(
        "member_id",
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "sub_account_id",
        UUID(as_uuid=True),
        ForeignKey("sub_accounts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class SubAccount(Base):
    """An isolated workspace for a single business entity."""
    __tablename__ = "sub_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String(255), nullable=False)
    industry_type = Column(
        SQLEnum(IndustryType), default=IndustryType.OTHER, nullable=False
    )
    logo_url = Column(String(1024))
    custom_domain = Column(String(255))

    # Localization / compliance (used by quiet-hours scheduling)
    timezone = Column(String(50), default="America/Denver", nullable=False)
    quiet_hours_start = Column(String(5), default="08:00", nullable=False)  # local HH:MM
    quiet_hours_end = Column(String(5), default="20:00", nullable=False)

    # Sender identity for outbound channels (white-label, per business)
    from_name = Column(String(255))
    reply_to_email = Column(String(255))
    twilio_phone_number = Column(String(30), index=True)

    # Internal owner notification target (speed-to-lead dispatch)
    owner_email = Column(String(255))
    owner_phone = Column(String(30))

    settings = Column(JSONB, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agency = relationship("Agency", back_populates="sub_accounts")
    members = relationship(
        "Member", secondary=member_sub_accounts, back_populates="sub_accounts"
    )

    __table_args__ = (
        UniqueConstraint("agency_id", "name", name="uq_sub_account_agency_name"),
    )


class Member(Base):
    """A person with access to one or more sub-accounts within an agency."""
    __tablename__ = "members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    role = Column(SQLEnum(MemberRole), default=MemberRole.MEMBER, nullable=False)

    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agency = relationship("Agency", back_populates="members")
    sub_accounts = relationship(
        "SubAccount", secondary=member_sub_accounts, back_populates="members"
    )


@declarative_mixin
class TenantMixin:
    """Adds the mandatory sub_account_id scoping column to a model.

    Any model carrying this mixin is automatically filtered by the active
    sub-account in every ORM SELECT (see app.core.tenancy).
    """

    @declared_attr
    def sub_account_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("sub_accounts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
