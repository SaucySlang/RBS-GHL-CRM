import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.tenancy import TenantMixin


class AIReceptionistConfig(TenantMixin, Base):
    """Per-sub-account AI persona: each business runs its own isolated
    receptionist with its own context and provider preference."""
    __tablename__ = "ai_receptionist_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # The persona + cleaned business knowledge fed to the LLM
    prompt_context = Column(Text, default="")

    # anthropic | openai | ollama (falls back down the chain automatically)
    model_provider = Column(String(30), default="anthropic", nullable=False)

    web_chat_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sub_account_id", name="uq_ai_config_sub_account"),
    )


class ChatSession(TenantMixin, Base):
    """A web-chat widget session. Starts anonymous; once the agent extracts
    a name + phone it is promoted into a concrete Contact."""
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    visitor_key = Column(String(64), nullable=False, index=True)
    # [{"role": "user"|"assistant", "content": "...", "at": iso}]
    transcript = Column(JSONB, default=list, nullable=False)

    contact_id = Column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )

    # Live extraction scratchpad (name/phone gathered so far)
    extracted = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "sub_account_id", "visitor_key", name="uq_chat_session_visitor"
        ),
    )
