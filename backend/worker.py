from __future__ import annotations

from datetime import datetime
from arq.connections import RedisSettings
from config import settings


async def run_task_job(
    ctx: dict,
    task_id: str,
    repo_id: str,
    issue_number: int | None = None,
    repo_full_name: str | None = None,
    skill_name: str | None = None,
    api_key_id: str | None = None,
) -> None:
    from database import engine
    from sqlmodel import Session
    from models.task import Task, Repo
    from agent.orchestrator import run_task

    with Session(engine) as db:
        task = db.get(Task, task_id)
        repo = db.get(Repo, repo_id)

    if not task or not repo:
        return

    await run_task(
        task,
        repo,
        issue_number=issue_number,
        repo_full_name=repo_full_name,
        skill_name=skill_name,
        api_key_id=api_key_id,
    )


async def startup(ctx: dict) -> None:
    from database import init_db
    init_db()
    _reconcile_orphaned_tasks()


def _reconcile_orphaned_tasks() -> None:
    from datetime import timedelta
    from database import engine
    from sqlmodel import Session, select
    from models.task import Task, Phase

    cutoff = datetime.utcnow() - timedelta(minutes=10)
    terminal = {Phase.DONE, Phase.FAILED}

    with Session(engine) as db:
        stale = db.exec(
            select(Task)
            .where(Task.phase.not_in(terminal))
            .where(Task.updated_at < cutoff)
        ).all()

        for task in stale:
            prev_phase = task.phase.value if task.phase else "unknown"
            task.phase = Phase.FAILED
            task.error = f"worker crashed during {prev_phase}"
            db.add(task)

        if stale:
            db.commit()


class WorkerSettings:
    functions = [run_task_job]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 3600
