"""In-process pub/sub for real-time pipeline sync across browser tabs.

Connections are grouped per sub-account so events never cross workspaces.
"""
import asyncio
import json
import logging
import uuid
from collections import defaultdict
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class PipelineConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[uuid.UUID, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, sub_account_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[sub_account_id].add(websocket)

    async def disconnect(self, sub_account_id: uuid.UUID, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[sub_account_id].discard(websocket)

    async def broadcast(self, sub_account_id: uuid.UUID, event: Dict[str, Any]) -> None:
        payload = json.dumps(event, default=str)
        async with self._lock:
            sockets = list(self._connections.get(sub_account_id, ()))
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                await self.disconnect(sub_account_id, ws)


pipeline_manager = PipelineConnectionManager()


def deal_event(event_type: str, deal) -> Dict[str, Any]:
    return {
        "type": event_type,
        "deal": {
            "id": str(deal.id),
            "sub_account_id": str(deal.sub_account_id),
            "contact_id": str(deal.contact_id) if deal.contact_id else None,
            "title": deal.title,
            "value": float(deal.value or 0),
            "stage": deal.stage.value if hasattr(deal.stage, "value") else deal.stage,
            "lost_reason": deal.lost_reason,
            "position": deal.position,
            "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
        },
    }
