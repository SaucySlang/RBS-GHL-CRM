"""Workflow / automation management (tenant-scoped)."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.tenancy import require_sub_account
from app.models import Contact, SubAccount
from app.models.automations import (
    ExecutionState, StepType, Workflow, WorkflowExecutionLog, WorkflowStep,
)
from app.services.workflow_engine import (
    create_speed_to_lead_workflow, trigger_workflows,
)

router = APIRouter()

# ============ SCHEMAS ============

class StepCreate(BaseModel):
    step_type: StepType
    config: dict = {}

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str = "form_submission"
    trigger_config: dict = {}
    is_active: bool = True
    steps: List[StepCreate] = []

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    is_active: Optional[bool] = None

class StepResponse(BaseModel):
    id: UUID
    order: int
    step_type: StepType
    config: dict

    class Config:
        from_attributes = True

class WorkflowResponse(BaseModel):
    id: UUID
    sub_account_id: UUID
    name: str
    description: Optional[str]
    trigger_type: str
    is_active: bool
    steps: List[StepResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExecutionLogResponse(BaseModel):
    id: UUID
    execution_id: UUID
    workflow_id: UUID
    step_id: Optional[UUID]
    contact_id: Optional[UUID]
    state: ExecutionState
    detail: Optional[str]
    scheduled_for: datetime
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# ============ ROUTES ============

@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Workflow)
        .where(Workflow.sub_account_id == sub_account.id)
        .options(selectinload(Workflow.steps))
        .order_by(Workflow.created_at.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    workflow = Workflow(
        sub_account_id=sub_account.id,
        name=data.name,
        description=data.description,
        trigger_type=data.trigger_type,
        trigger_config=data.trigger_config,
        is_active=data.is_active,
    )
    db.add(workflow)
    await db.flush()
    for index, step in enumerate(data.steps):
        db.add(
            WorkflowStep(
                workflow_id=workflow.id,
                order=index,
                step_type=step.step_type,
                config=step.config,
            )
        )
    await db.flush()
    return await _load_workflow(db, workflow.id, sub_account.id)

@router.post("/speed-to-lead", response_model=WorkflowResponse, status_code=201)
async def create_speed_to_lead(
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """One-click creation of the canonical speed-to-lead chain."""
    workflow = await create_speed_to_lead_workflow(db, sub_account.id)
    return await _load_workflow(db, workflow.id, sub_account.id)

@router.get("/logs", response_model=List[ExecutionLogResponse])
async def list_execution_logs(
    workflow_id: Optional[UUID] = None,
    state: Optional[ExecutionState] = None,
    limit: int = 100,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    query = select(WorkflowExecutionLog).where(
        WorkflowExecutionLog.sub_account_id == sub_account.id
    )
    if workflow_id:
        query = query.where(WorkflowExecutionLog.workflow_id == workflow_id)
    if state:
        query = query.where(WorkflowExecutionLog.state == state)
    query = query.order_by(WorkflowExecutionLog.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    return await _load_workflow(db, workflow_id, sub_account.id)

@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    data: WorkflowUpdate,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    workflow = await _load_workflow(db, workflow_id, sub_account.id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(workflow, field, value)
    workflow.updated_at = datetime.utcnow()
    await db.flush()
    return await _load_workflow(db, workflow_id, sub_account.id)

@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    workflow = await _load_workflow(db, workflow_id, sub_account.id)
    await db.delete(workflow)
    return {"deleted": True, "id": str(workflow_id)}

@router.post("/{workflow_id}/trigger/{contact_id}")
async def manually_trigger(
    workflow_id: UUID,
    contact_id: UUID,
    sub_account: SubAccount = Depends(require_sub_account),
    db: AsyncSession = Depends(get_db),
):
    """Manually enroll a contact (testing / one-off runs)."""
    workflow = await _load_workflow(db, workflow_id, sub_account.id)
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id, Contact.sub_account_id == sub_account.id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    execution_ids = await trigger_workflows(
        db,
        sub_account_id=sub_account.id,
        trigger_type=workflow.trigger_type,
        contact=contact,
        context={"manual": True},
    )
    return {"triggered": True, "executions": [str(e) for e in execution_ids]}

# ============ HELPERS ============

async def _load_workflow(db: AsyncSession, workflow_id: UUID, sub_account_id: UUID) -> Workflow:
    result = await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow_id, Workflow.sub_account_id == sub_account_id)
        .options(selectinload(Workflow.steps))
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
