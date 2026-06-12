import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey,
    Enum as SQLEnum, Index, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.tenancy import TenantMixin


class ExecutionState(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED_COMPLIANCE = "SKIPPED_COMPLIANCE"
    PAUSED_QUIET_HOURS = "PAUSED_QUIET_HOURS"


class StepType(str, enum.Enum):
    SEND_SMS = "send_sms"
    SEND_EMAIL = "send_email"
    WAIT = "wait"
    NOTIFY_OWNER = "notify_owner"


class Workflow(TenantMixin, Base):
    """An automation: a trigger plus an ordered chain of steps."""
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    # form_submission, contact_created, inbound_sms, manual
    trigger_type = Column(String(50), nullable=False, index=True)
    trigger_config = Column(JSONB, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        order_by="WorkflowStep.order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_workflows_sub_account_trigger", "sub_account_id", "trigger_type"),
    )


class WorkflowStep(Base):
    """One node in a workflow chain (tenancy inherited via the workflow)."""
    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order = Column(Integer, nullable=False, default=0)
    step_type = Column(SQLEnum(StepType), nullable=False)
    # send_sms: {"body": "..."} (merge tags supported)
    # send_email: {"subject": "...", "body": "..."}
    # wait: {"seconds": 60}
    # notify_owner: {"message": "..."}
    config = Column(JSONB, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="steps")

    __table_args__ = (
        UniqueConstraint("workflow_id", "order", name="uq_workflow_step_order"),
    )


class WorkflowExecutionLog(TenantMixin, Base):
    """Per-step execution record. One workflow run shares an execution_id."""
    __tablename__ = "workflow_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_steps.id", ondelete="CASCADE"),
        nullable=True,
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    state = Column(
        SQLEnum(ExecutionState), default=ExecutionState.PENDING, nullable=False
    )
    detail = Column(Text)
    context = Column(JSONB, default=dict)

    # When the background runner should (re)attempt this step
    scheduled_for = Column(DateTime, default=datetime.utcnow, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    workflow = relationship("Workflow")
    step = relationship("WorkflowStep")

    __table_args__ = (
        Index("ix_execution_logs_due", "state", "scheduled_for"),
    )


class ComplianceRegistry(TenantMixin, Base):
    """A2P opt-out registry: one row per phone number per sub-account."""
    __tablename__ = "compliance_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    phone_number = Column(String(30), nullable=False)  # normalized last-10 digits
    has_opted_out = Column(Boolean, default=False, nullable=False)
    opted_out_at = Column(DateTime)
    opt_out_source = Column(String(50))  # sms_keyword, manual, carrier

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "sub_account_id", "phone_number", name="uq_compliance_sub_account_phone"
        ),
    )
