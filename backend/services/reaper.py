from __future__ import annotations

import asyncio
import logging
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sqlmodel import Session, select

from config import settings
from database import engine
from models.task import Task, Phase

_log = logging.getLogger(__name__)

_TERMINAL_PHASES = {Phase.DONE, Phase.FAILED}
_DEFAULT_TTL_HOURS = 24


async def reap_workspaces(ttl_hours: int = _DEFAULT_TTL_HOURS) -> int:
    root = Path(settings.workspace_base_dir)
    if not root.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)
    removed = 0

    with Session(engine) as session:
        for candidate in root.iterdir():
            if not candidate.is_dir():
                continue

            task_id = candidate.name
            task = session.get(Task, task_id)

            if task is None:
                _log.info("reaper: removing orphaned workspace %s", task_id)
                await _rmtree(candidate)
                removed += 1
                continue

            if task.phase in _TERMINAL_PHASES:
                completed = task.completed_at
                if completed is None:
                    completed = task.updated_at
                if completed.tzinfo is None:
                    completed = completed.replace(tzinfo=timezone.utc)
                if completed < cutoff:
                    _log.info("reaper: removing completed workspace %s (phase=%s)", task_id, task.phase)
                    await _rmtree(candidate)
                    removed += 1

    return removed


async def _rmtree(path: Path) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, shutil.rmtree, str(path), True)


async def _reaper_loop(interval_seconds: int = 3600, ttl_hours: int = _DEFAULT_TTL_HOURS) -> None:
    while True:
        try:
            removed = await reap_workspaces(ttl_hours=ttl_hours)
            if removed:
                _log.info("reaper: removed %d workspace(s)", removed)
        except Exception:
            _log.exception("reaper: unexpected error")
        await asyncio.sleep(interval_seconds)


def start_reaper(interval_seconds: int = 3600, ttl_hours: int = _DEFAULT_TTL_HOURS) -> asyncio.Task:
    return asyncio.create_task(_reaper_loop(interval_seconds=interval_seconds, ttl_hours=ttl_hours))
