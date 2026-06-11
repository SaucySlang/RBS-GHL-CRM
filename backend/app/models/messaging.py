import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.tenancy import TenantMixin

class Conversation(TenantMixin, Base):
    """Threaded conversations with contacts."""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    channel = Column(String(20), default="sms")
    status = Column(String(20), default="open")  # open, closed, snoozed

    # AI handling
    ai_enabled = Column(Boolean, default=True)
    ai_context = Column(JSONB, default=dict)

    # Tracking
    last_message_at = Column(DateTime)
    last_message_preview = Column(String(255))
    unread_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = relationship("Contact", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")

    __table_args__ = (
        Index("ix_conversations_sub_account_status", "sub_account_id", "status"),
    )

class Message(TenantMixin, Base):
    """Individual messages (SMS, email, etc.)."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))

    # Message details
    channel = Column(String(20), nullable=False)  # sms, email, voice
    direction = Column(String(10), nullable=False)  # inbound, outbound
    status = Column(String(20), default="pending")

    # Content
    from_address = Column(String(255))
    to_address = Column(String(255))
    subject = Column(String(500))  # for email
    body = Column(Text, nullable=False)

    # Provider tracking
    provider = Column(String(50))  # twilio, sendgrid, etc.
    provider_id = Column(String(255))  # Twilio SID, etc.
    provider_status = Column(String(50))

    # AI
    ai_generated = Column(Boolean, default=False)
    ai_model = Column(String(100))

    # Cost tracking
    cost = Column(Integer, default=0)  # in cents
    segments = Column(Integer, default=1)

    # Metadata ("metadata" is reserved by SQLAlchemy declarative)
    extra_data = Column("metadata", JSONB, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)

    # Relationships
    contact = relationship("Contact", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_sub_account_created", "sub_account_id", "created_at"),
        Index("ix_messages_conversation", "conversation_id"),
        Index("ix_messages_provider_id", "provider_id"),
    )

class MessageTemplate(TenantMixin, Base):
    """Reusable message templates."""
    __tablename__ = "message_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False)
    channel = Column(String(20), nullable=False)  # sms, email

    subject = Column(String(500))  # for email
    body = Column(Text, nullable=False)

    # Personalization tokens available
    tokens = Column(JSONB, default=list)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
