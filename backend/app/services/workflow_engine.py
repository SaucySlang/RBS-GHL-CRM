"""Workflow execution engine.

A trigger creates one execution (shared execution_id) and a PENDING log row
for the first step. The background runner picks up due rows and executes
them; each step schedules its successor. Every attempt passes through:

1. The compliance pre-flight (opt-out registry) -> SKIPPED_COMPLIANCE aborts
   the rest of the run.
2. The quiet-hours window -> PAUSED_QUIET_HOURS reschedules the same step
   for the moment the sub-account's local window reopens.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, SubAccount
from app.models.automations import (
    ComplianceRegistry,  # noqa: F401  (registered with metadata)
    ExecutionState,
    StepType,
    Workflow,
    WorkflowExecutionLog,
    WorkflowStep,
)
from app.services.compliance import ComplianceBlockedError, assert_can_message
from app.services.interpolation import render_merge_tags
from app.services.quiet_hours import next_send_time

logger = logging.getLogger(__name__)


async def trigger_workflows(
    db: AsyncSession,
    sub_account_id: uuid.UUID,
    trigger_type: str,
    contact: Optional[Contact],
    context: Optional[dict] = None,
) -> list[uuid.UUID]:
    """Enroll a contact in every active workflow bound to this trigger.
    Returns the execution ids started."""
    result = await db.execute(
        select(Workflow).where(
            Workflow.sub_account_id == sub_account_id,
            Workflow.trigger_type == trigger_type,
            Workflow.is_active.is_(True),
        )
    )
    workflows = result.scalars().all()

    execution_ids: list[uuid.UUID] = []
    for workflow in workflows:
        first_step = await _get_step(db, workflow.id, order=0)
        if first_step is None:
            continue
        execution_id = uuid.uuid4()
        db.add(
            WorkflowExecutionLog(
                sub_account_id=sub_account_id,
                execution_id=execution_id,
                workflow_id=workflow.id,
                step_id=first_step.id,
                contact_id=contact.id if contact else None,
                state=ExecutionState.PENDING,
                context=context or {},
                scheduled_for=datetime.utcnow(),
            )
        )
        execution_ids.append(execution_id)

    if execution_ids:
        await db.flush()
        logger.info(
            "Triggered %d workflow(s) for %s in sub-account %s",
            len(execution_ids), trigger_type, sub_account_id,
        )
    return execution_ids


async def process_due_steps(db: AsyncSession, limit: int = 50) -> int:
    """Execute every due step (PENDING or quiet-hours-paused whose window
    has reopened). Called by the background runner; returns count handled."""
    now = datetime.utcnow()
    result = await db.execute(
        select(WorkflowExecutionLog)
        .where(
            WorkflowExecutionLog.state.in_(
                [ExecutionState.PENDING, ExecutionState.PAUSED_QUIET_HOURS]
            ),
            WorkflowExecutionLog.scheduled_for <= now,
        )
        .order_by(WorkflowExecutionLog.scheduled_for)
        .limit(limit)
        .execution_options(skip_tenant_scope=True)
    )
    due_logs = result.scalars().all()

    for log in due_logs:
        try:
            await _execute_step(db, log)
        except Exception:
            logger.exception("Workflow step %s crashed", log.id)
            log.state = ExecutionState.FAILED
            log.detail = "Internal error during execution"
            log.completed_at = datetime.utcnow()
        await db.flush()

    return len(due_logs)


async def _execute_step(db: AsyncSession, log: WorkflowExecutionLog) -> None:
    step = (
        await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.id == log.step_id)
            .execution_options(skip_tenant_scope=True)
        )
    ).scalar_one_or_none()
    sub_account = (
        await db.execute(
            select(SubAccount).where(SubAccount.id == log.sub_account_id)
        )
    ).scalar_one_or_none()
    contact = None
    if log.contact_id:
        contact = (
            await db.execute(
                select(Contact)
                .where(Contact.id == log.contact_id)
                .execution_options(skip_tenant_scope=True)
            )
        ).scalar_one_or_none()

    if step is None or sub_account is None:
        log.state = ExecutionState.FAILED
        log.detail = "Step or sub-account no longer exists"
        log.completed_at = datetime.utcnow()
        return

    config = step.config or {}

    # ---- WAIT nodes complete instantly and delay the successor ----
    if step.step_type == StepType.WAIT:
        delay = int(config.get("seconds", 60))
        log.state = ExecutionState.COMPLETED
        log.detail = f"Waited node: next step in {delay}s"
        log.completed_at = datetime.utcnow()
        await _schedule_next(db, log, step, delay_seconds=delay)
        return

    # ---- Owner notification: internal dispatch, exempt from quiet hours ----
    if step.step_type == StepType.NOTIFY_OWNER:
        await _notify_owner(db, sub_account, contact, config, log)
        await _schedule_next(db, log, step)
        return

    # ---- Outbound SMS / email to the contact ----
    channel = "sms" if step.step_type == StepType.SEND_SMS else "email"

    if contact is None:
        log.state = ExecutionState.FAILED
        log.detail = "No contact attached to this execution"
        log.completed_at = datetime.utcnow()
        return

    # 1. Compliance pre-flight: abort the whole run on a registry hit
    try:
        await assert_can_message(db, sub_account.id, contact, channel)
    except ComplianceBlockedError as exc:
        log.state = ExecutionState.SKIPPED_COMPLIANCE
        log.detail = str(exc)
        log.completed_at = datetime.utcnow()
        logger.info("Execution %s aborted: %s", log.execution_id, exc)
        return  # no successor scheduled — execution aborted

    # 2. Quiet hours: pause this same step until the window reopens
    reopen_at = next_send_time(sub_account)
    if reopen_at is not None:
        log.state = ExecutionState.PAUSED_QUIET_HOURS
        log.scheduled_for = reopen_at
        log.detail = f"Outside send window; resuming at {reopen_at.isoformat()}Z"
        logger.info(
            "Execution %s paused for quiet hours until %s", log.execution_id, reopen_at
        )
        return

    # 3. Interpolate merge tags against live rows, then transmit
    from app.services.messaging import send_to_contact

    body = render_merge_tags(
        config.get("body", ""), contact=contact, sub_account=sub_account
    )
    subject = render_merge_tags(
        config.get("subject", ""), contact=contact, sub_account=sub_account
    )

    message = await send_to_contact(
        db=db,
        sub_account=sub_account,
        contact=contact,
        channel=channel,
        body=body,
        subject=subject or None,
        skip_compliance=True,  # pre-flight already done above
    )

    if message.status == "failed":
        log.state = ExecutionState.FAILED
        log.detail = f"Provider dispatch failed for {channel}"
        log.completed_at = datetime.utcnow()
        return

    log.state = ExecutionState.COMPLETED
    log.detail = f"Sent {channel} message {message.id}"
    log.completed_at = datetime.utcnow()
    await _schedule_next(db, log, step)


async def _notify_owner(
    db: AsyncSession,
    sub_account: SubAccount,
    contact: Optional[Contact],
    config: dict,
    log: WorkflowExecutionLog,
) -> None:
    """Internal owner dispatch (email and/or SMS to the workspace owner)."""
    template = config.get(
        "message",
        "New lead for {{sub_account.name}}: {{contact.full_name}} "
        "({{contact.phone}} / {{contact.email}})",
    )
    body = render_merge_tags(template, contact=contact, sub_account=sub_account)

    from app.services.messaging import _dispatch_email, _dispatch_sms, resolve_sms_sender

    dispatched = []
    if sub_account.owner_email:
        status, _ = await _dispatch_email(
            sub_account.owner_email,
            f"[{sub_account.name}] New lead notification",
            body,
            from_email=None if not sub_account.reply_to_email else sub_account.reply_to_email,
            from_name=sub_account.from_name or sub_account.name,
            reply_to=None,
        )
        dispatched.append(f"email:{status}")
    if sub_account.owner_phone:
        status, _ = await _dispatch_sms(
            sub_account.owner_phone, body, resolve_sms_sender(sub_account)
        )
        dispatched.append(f"sms:{status}")

    log.state = ExecutionState.COMPLETED
    log.detail = (
        f"Owner notified ({', '.join(dispatched)})" if dispatched
        else "Owner notification skipped: no owner contact configured"
    )
    log.completed_at = datetime.utcnow()


async def _schedule_next(
    db: AsyncSession,
    log: WorkflowExecutionLog,
    current_step: WorkflowStep,
    delay_seconds: int = 0,
) -> None:
    next_step = await _get_step(db, current_step.workflow_id, current_step.order + 1)
    if next_step is None:
        return
    db.add(
        WorkflowExecutionLog(
            sub_account_id=log.sub_account_id,
            execution_id=log.execution_id,
            workflow_id=log.workflow_id,
            step_id=next_step.id,
            contact_id=log.contact_id,
            state=ExecutionState.PENDING,
            context=log.context,
            scheduled_for=datetime.utcnow() + timedelta(seconds=delay_seconds),
        )
    )


async def _get_step(
    db: AsyncSession, workflow_id: uuid.UUID, order: int
) -> Optional[WorkflowStep]:
    result = await db.execute(
        select(WorkflowStep)
        .where(WorkflowStep.workflow_id == workflow_id, WorkflowStep.order == order)
        .execution_options(skip_tenant_scope=True)
    )
    return result.scalar_one_or_none()


# ============ Speed-to-Lead sequence builder ============

SPEED_TO_LEAD_NAME = "Speed-to-Lead"


async def create_speed_to_lead_workflow(
    db: AsyncSession, sub_account_id: uuid.UUID
) -> Workflow:
    """Programmatically build the canonical sequence:

    Form Submission -> Immediate SMS -> Immediate Email
        -> Wait (1 minute) -> Internal Owner Notification
    """
    workflow = Workflow(
        sub_account_id=sub_account_id,
        name=SPEED_TO_LEAD_NAME,
        description=(
            "Instant response the moment a form is submitted: SMS + email to "
            "the lead, then an internal owner alert one minute later."
        ),
        trigger_type="form_submission",
        is_active=True,
    )
    db.add(workflow)
    await db.flush()

    steps = [
        WorkflowStep(
            workflow_id=workflow.id,
            order=0,
            step_type=StepType.SEND_SMS,
            config={
                "body": (
                    "Hi {{contact.first_name}}, thanks for reaching out to "
                    "{{sub_account.name}}! We just got your message and will "
                    "call you shortly. Reply STOP to opt out."
                )
            },
        ),
        WorkflowStep(
            workflow_id=workflow.id,
            order=1,
            step_type=StepType.SEND_EMAIL,
            config={
                "subject": "We got your message — {{sub_account.name}}",
                "body": (
                    "Hi {{contact.first_name}},\n\n"
                    "Thanks for contacting {{sub_account.name}}. A real human "
                    "is being notified right now and will reach out shortly.\n\n"
                    "— The {{sub_account.name}} team"
                ),
            },
        ),
        WorkflowStep(
            workflow_id=workflow.id,
            order=2,
            step_type=StepType.WAIT,
            config={"seconds": 60},
        ),
        WorkflowStep(
            workflow_id=workflow.id,
            order=3,
            step_type=StepType.NOTIFY_OWNER,
            config={
                "message": (
                    "Speed-to-lead: {{contact.full_name}} just submitted a form "
                    "for {{sub_account.name}}. Phone: {{contact.phone}} · "
                    "Email: {{contact.email}}. First-touch SMS/email already sent."
                )
            },
        ),
    ]
    db.add_all(steps)
    await db.flush()
    await db.refresh(workflow)
    return workflow
