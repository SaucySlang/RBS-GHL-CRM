"""WebSocket endpoint for real-time pipeline sync across open tabs."""
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.tenancy import SubAccount
from app.services.pipeline_events import pipeline_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/pipeline")
async def pipeline_websocket(websocket: WebSocket, sub_account_id: str):
    """Clients connect with ?sub_account_id=<uuid> (browsers cannot send
    custom headers during the WS handshake). Events are only ever broadcast
    within the same sub-account group."""
    try:
        tenant_id = uuid.UUID(sub_account_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SubAccount).where(SubAccount.id == tenant_id))
        if result.scalar_one_or_none() is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await pipeline_manager.connect(tenant_id, websocket)
    try:
        while True:
            # Keep the socket open; clients send pings, server pushes events.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await pipeline_manager.disconnect(tenant_id, websocket)
