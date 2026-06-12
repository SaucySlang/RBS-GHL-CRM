"""Local background runner.

Polls for due workflow steps (including quiet-hours-paused steps whose
window has reopened) every few seconds and executes them. Runs as an
asyncio task inside the API process — no external worker required.
"""
import asyncio
import logging

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5

_runner_task: asyncio.Task | None = None


async def _run_forever() -> None:
    from app.services.workflow_engine import process_due_steps

    logger.info("Workflow runner started (poll every %ss)", POLL_INTERVAL_SECONDS)
    while True:
        try:
            async with AsyncSessionLocal() as db:
                handled = await process_due_steps(db)
                if handled:
                    await db.commit()
                    logger.info("Workflow runner executed %d step(s)", handled)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Workflow runner cycle failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def start_scheduler() -> None:
    global _runner_task
    if _runner_task is None or _runner_task.done():
        _runner_task = asyncio.create_task(_run_forever())


async def stop_scheduler() -> None:
    global _runner_task
    if _runner_task is not None:
        _runner_task.cancel()
        try:
            await _runner_task
        except asyncio.CancelledError:
            pass
        _runner_task = None
