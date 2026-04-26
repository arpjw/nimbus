import asyncio
import json
import logging
import re
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session, select

from agent.orchestrator import run_task
from api.ws import get_or_create_queue, pump_queue_to_ws
from database import engine
from models.automation import Automation
from models.task import Task, Repo

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


def _get_nested(obj: dict, path: str) -> str | None:
    parts = path.split(".")
    current = obj
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return str(current) if current is not None else None


def _matches(automation: Automation, payload: dict) -> bool:
    try:
        config = json.loads(automation.trigger_config)
    except (json.JSONDecodeError, TypeError):
        return False

    match_rules: dict = config.get("match", {})
    for key_path, expected in match_rules.items():
        actual = _get_nested(payload, key_path)
        if actual != str(expected):
            return False
    return True


def _render_task(automation: Automation, payload: dict) -> str:
    template = automation.task_template

    def replacer(m: re.Match) -> str:
        path = m.group(1).strip()
        if path.startswith("payload."):
            path = path[len("payload."):]
        value = _get_nested(payload, path)
        return value if value is not None else m.group(0)

    return re.sub(r"\{\{([^}]+)\}\}", replacer, template)


def _queue_task(task: Task, repo: Repo) -> None:
    queue = get_or_create_queue(task.id)
    asyncio.create_task(run_task(task, repo, queue))
    asyncio.create_task(pump_queue_to_ws(task.id))


class AutomationEngine:
    def evaluate_webhook(self, payload: dict, headers: dict) -> list[Automation]:
        with Session(engine) as session:
            all_automations = session.exec(
                select(Automation).where(
                    Automation.enabled == True,
                    Automation.trigger_type == "webhook",
                )
            ).all()
            return [a for a in all_automations if _matches(a, payload)]

    def render_task(self, automation: Automation, payload: dict) -> str:
        return _render_task(automation, payload)

    async def trigger_automation(self, automation: Automation, context: dict) -> str | None:
        with Session(engine) as session:
            repo = session.get(Repo, automation.repo_id)
            if not repo:
                logger.warning("Repo not found for automation %s", automation.id)
                return None

            description = _render_task(automation, context)
            task = Task(
                workspace_id=repo.workspace_id,
                repo_id=repo.id,
                description=description,
            )
            session.add(task)

            db_automation = session.get(Automation, automation.id)
            if db_automation:
                db_automation.last_triggered_at = datetime.utcnow()
                session.add(db_automation)

            session.commit()
            session.refresh(task)
            task_id = task.id
            _queue_task(task, repo)

            if db_automation:
                with Session(engine) as s2:
                    a = s2.get(Automation, automation.id)
                    if a:
                        a.last_task_id = task_id
                        s2.add(a)
                        s2.commit()

        return task_id

    def schedule_all(self) -> None:
        if not _scheduler.running:
            _scheduler.start()

        for job in _scheduler.get_jobs():
            job.remove()

        with Session(engine) as session:
            cron_automations = session.exec(
                select(Automation).where(
                    Automation.enabled == True,
                    Automation.trigger_type == "cron",
                )
            ).all()

            for automation in cron_automations:
                try:
                    config = json.loads(automation.trigger_config)
                    cron_expr: str = config.get("schedule", "")
                    if not cron_expr:
                        continue

                    parts = cron_expr.split()
                    if len(parts) != 5:
                        continue

                    minute, hour, day, month, day_of_week = parts
                    automation_id = automation.id

                    _scheduler.add_job(
                        _run_cron_automation,
                        "cron",
                        args=[automation_id],
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week,
                        id=automation_id,
                        replace_existing=True,
                    )
                    logger.info("Scheduled cron automation %s: %s", automation.name, cron_expr)
                except Exception as exc:
                    logger.error("Failed to schedule automation %s: %s", automation.id, exc)


async def _run_cron_automation(automation_id: str) -> None:
    engine_instance = AutomationEngine()
    with Session(engine) as session:
        automation = session.get(Automation, automation_id)
        if not automation or not automation.enabled:
            return
    await engine_instance.trigger_automation(automation, {})
