import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.tenancy import TenantMixin

# ============ ENUMS ============

class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"

class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class MessageChannel(str, enum.Enum):
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    WHATSAPP = "whatsapp"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"

# ============ CORE CRM MODELS (tenant-scoped) ============

class Contact(TenantMixin, Base):
    """CRM contacts/leads. Strictly scoped to a sub-account."""
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core fields
    email = Column(String(255))
    phone = Column(String(30))
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Status & Compliance
    status = Column(SQLEnum(ContactStatus), default=ContactStatus.ACTIVE)
    sms_consent = Column(Boolean, default=False)
    email_consent = Column(Boolean, default=False)
    do_not_disturb = Column(Boolean, default=False)

    # Custom fields
    custom_fields = Column(JSONB, default=dict)
    tags = Column(ARRAY(String), default=list)

    # Source tracking
    source = Column(String(100))
    source_id = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contacted_at = Column(DateTime)

    # Relationships
    messages = relationship("Message", back_populates="contact")
    conversations = relationship("Conversation", back_populates="contact")
    notes = relationship("Note", back_populates="contact", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="contact")

    __table_args__ = (
        Index("ix_contacts_sub_account_phone", "sub_account_id", "phone"),
        Index("ix_contacts_sub_account_email", "sub_account_id", "email"),
        Index("ix_contacts_tags", "tags", postgresql_using="gin"),
    )

class Note(TenantMixin, Base):
    """Free-form notes attached to a contact."""
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    body = Column(Text, nullable=False)
    author = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = relationship("Contact", back_populates="notes")

class Tag(TenantMixin, Base):
    """Reusable tags for contacts."""
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#8B5CF6")

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sub_account_id", "name", name="uq_tag_sub_account_name"),
    )
