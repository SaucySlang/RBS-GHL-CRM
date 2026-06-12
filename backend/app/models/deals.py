import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Index, Numeric, Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.tenancy import TenantMixin


class DealStage(str, enum.Enum):
    NEW_LEAD = "new_lead"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    WON = "won"
    LOST = "lost"


class Deal(TenantMixin, Base):
    """A deal moving through the 6-stage pipeline. Strictly sub-account scoped."""
    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title = Column(String(255), nullable=False)
    value = Column(Numeric(12, 2), default=0, nullable=False)
    stage = Column(SQLEnum(DealStage), default=DealStage.NEW_LEAD, nullable=False)

    # Required when a deal is dragged into the Lost column
    lost_reason = Column(Text)

    # Ordering within a Kanban column
    position = Column(Float, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = relationship("Contact", back_populates="deals")

    __table_args__ = (
        Index("ix_deals_sub_account_stage", "sub_account_id", "stage"),
    )
