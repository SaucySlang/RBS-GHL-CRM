"""Strict workspace isolation.

Every API request must carry an `X-SubAccount-ID` header. A FastAPI
dependency resolves and validates the sub-account, then places its id in a
ContextVar. A SQLAlchemy `do_orm_execute` listener reads that ContextVar and
injects a row-level criteria (`sub_account_id == <active>`) into every ORM
SELECT / UPDATE / DELETE that touches a tenant-scoped model — including
relationship lazy-loads — so cross-tenant leakage is impossible even if a
route forgets to filter explicitly.
"""
import uuid
from contextvars import ContextVar
from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, with_loader_criteria

from app.core.database import get_db
from app.models.tenancy import SubAccount, TenantMixin

# The active tenant for the current request/task. None = no scoping
# (system context: startup, seeding, webhook resolution).
current_sub_account_id: ContextVar[Optional[uuid.UUID]] = ContextVar(
    "current_sub_account_id", default=None
)


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_scope(execute_state) -> None:
    """Inject the row-level tenant filter into every ORM statement."""
    if execute_state.is_column_load or execute_state.is_relationship_load:
        # Loader criteria propagates to relationship loads automatically;
        # don't re-wrap internal loader statements.
        return
    if execute_state.execution_options.get("skip_tenant_scope", False):
        return

    tenant_id = current_sub_account_id.get()
    if tenant_id is None:
        return

    if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                TenantMixin,
                lambda cls: cls.sub_account_id == tenant_id,
                include_aliases=True,
            )
        )


async def require_sub_account(
    x_sub_account_id: str = Header(
        ..., alias="X-SubAccount-ID", description="Active sub-account (workspace) id"
    ),
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SubAccount, None]:
    """Resolve the active sub-account from the request header and activate
    row-level scoping for the lifetime of the request."""
    try:
        sub_account_id = uuid.UUID(x_sub_account_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400, detail="X-SubAccount-ID header must be a valid UUID"
        )

    result = await db.execute(
        select(SubAccount).where(SubAccount.id == sub_account_id)
    )
    sub_account = result.scalar_one_or_none()
    if sub_account is None:
        raise HTTPException(status_code=404, detail="Sub-account not found")

    token = current_sub_account_id.set(sub_account.id)
    try:
        yield sub_account
    finally:
        current_sub_account_id.reset(token)


def tenant_context(sub_account_id: uuid.UUID):
    """Context manager for activating tenant scope outside a request
    (background workers, webhook handlers, schedulers)."""

    class _TenantContext:
        def __enter__(self):
            self._token = current_sub_account_id.set(sub_account_id)
            return sub_account_id

        def __exit__(self, *exc):
            current_sub_account_id.reset(self._token)
            return False

    return _TenantContext()
