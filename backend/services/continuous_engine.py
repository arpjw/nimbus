from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlmodel import Session, select, func

from config import settings
from database import engine
from models.continuous import ContinuousSession
from models.task import Task, Repo
from models.token_usage import TokenUsage

_log = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 900


async def run_continuous_loop() -> None:
    while True:
        try:
            await _tick()
        except Exception as exc:
            _log.error("Continuous engine tick failed: %s", exc)
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)


async def _tick() -> None:
    with Session(engine) as session:
        active = session.exec(
            select(ContinuousSession).where(
                ContinuousSession.status == "active",
                ContinuousSession.expires_at > datetime.utcnow(),
            )
        ).all()

    for cs in active:
        try:
            await _process_session(cs)
        except Exception as exc:
            _log.error("Error processing continuous session %s: %s", cs.id, exc)


async def _process_session(cs: ContinuousSession) -> None:
    today_spend = _today_spend(cs.repo_id, cs.api_key_id)
    if today_spend >= cs.daily_spend_cap_usd:
        _log.info("Session %s: daily cap reached ($%.3f)", cs.id, today_spend)
        return

    with Session(engine) as session:
        repo = session.get(Repo, cs.repo_id)
    if not repo:
        return

    issues = await _fetch_issues(repo, cs.label_filter)
    dispatched = _already_dispatched(cs.repo_id, cs.started_at)

    for issue in issues:
        if today_spend >= cs.daily_spend_cap_usd:
            break
        issue_key = f"[#{issue['number']}]"
        if any(issue_key in desc for desc in dispatched):
            continue

        description = f"[#{issue['number']}] {issue['title']}\n\n{issue.get('body', '')[:2000]}".strip()
        await _dispatch_task(cs, repo, description)
        today_spend = _today_spend(cs.repo_id, cs.api_key_id)

    _update_last_checked(cs.id)


async def _dispatch_task(cs: ContinuousSession, repo: Repo, description: str) -> None:
    with Session(engine) as session:
        task = Task(
            workspace_id=repo.workspace_id,
            repo_id=repo.id,
            description=description,
            api_key_id=cs.api_key_id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id = task.id

    from agent.orchestrator import run_task
    from redis_client import get_redis
    import json

    redis_client = await get_redis()
    result_key = f"nimbus:approval-result:{task_id}"

    async def _auto_approve() -> None:
        await asyncio.sleep(3)
        task_check = _get_task(task_id)
        if task_check and task_check.confidence_score is not None:
            if task_check.confidence_score < cs.confidence_threshold:
                _log.info(
                    "Session %s: skipping task %s (confidence %.0f < threshold %d)",
                    cs.id, task_id, task_check.confidence_score, cs.confidence_threshold,
                )
                await redis_client.rpush(result_key, json.dumps({"approved": False}))
                return
        await redis_client.rpush(result_key, json.dumps({"approved": True}))

    asyncio.create_task(_auto_approve())
    asyncio.create_task(run_task(task, repo, api_key_id=cs.api_key_id))


def _get_task(task_id: str) -> Optional[Task]:
    with Session(engine) as session:
        return session.get(Task, task_id)


async def _fetch_issues(repo: Repo, label_filter: Optional[str]) -> list[dict]:
    if not settings.github_token or not repo.url:
        return []

    parts = repo.url.rstrip("/").split("/")
    if len(parts) < 2:
        return []
    owner, name = parts[-2], parts[-1]

    params: dict = {"state": "open", "per_page": 20}
    if label_filter:
        params["labels"] = label_filter

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{name}/issues",
                params=params,
                headers={
                    "Authorization": f"Bearer {settings.github_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            resp.raise_for_status()
            return [i for i in resp.json() if "pull_request" not in i]
    except Exception as exc:
        _log.warning("Failed to fetch issues for %s/%s: %s", owner, name, exc)
        return []


def _already_dispatched(repo_id: str, since: datetime) -> list[str]:
    with Session(engine) as session:
        tasks = session.exec(
            select(Task.description).where(
                Task.repo_id == repo_id,
                Task.created_at >= since,
            )
        ).all()
        return list(tasks)


def _today_spend(repo_id: str, api_key_id: str) -> float:
    midnight = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    with Session(engine) as session:
        task_ids = session.exec(
            select(Task.id).where(
                Task.repo_id == repo_id,
                Task.api_key_id == api_key_id,
                Task.created_at >= midnight,
            )
        ).all()
        if not task_ids:
            return 0.0
        total = session.exec(
            select(func.sum(TokenUsage.cost_usd)).where(
                TokenUsage.task_id.in_(task_ids)
            )
        ).one()
        return float(total or 0)


def _update_last_checked(session_id: str) -> None:
    with Session(engine) as session:
        cs = session.get(ContinuousSession, session_id)
        if cs:
            cs.last_checked_at = datetime.utcnow()
            cs.updated_at = datetime.utcnow()
            session.add(cs)
            session.commit()
