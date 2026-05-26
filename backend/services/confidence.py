from __future__ import annotations

import json
import logging
from typing import Optional

from sqlmodel import Session, select, func

from config import settings
from database import engine
from models.task import Task
from models.task_metrics import TaskMetrics
from models.token_usage import TokenUsage
from services.llm_client import instrumented_anthropic_client

_log = logging.getLogger(__name__)

_SYSTEM = """You are evaluating an implementation plan for a coding task.
Rate confidence from 0 to 100 based on:
1. Clarity of the task description (vague tasks score lower)
2. Whether the plan touches well-understood, well-tested files versus poorly-covered areas
3. Number and complexity of changes proposed
4. Whether similar tasks have succeeded on this repo in the past

Output only valid JSON: {"score": <int 0-100>, "reasoning": "<one paragraph>"}"""


async def score_confidence(
    task_id: str,
    description: str,
    plan_summary: str,
    files_touched: list[str],
    repo_id: str,
    api_key_id: Optional[str] = None,
) -> tuple[float, str]:
    historical_rate = _historical_success_rate(repo_id)

    context = f"""Task: {description}

Plan summary: {plan_summary}

Files to change: {", ".join(files_touched) if files_touched else "none listed"}

Historical success rate on this repo: {historical_rate:.0%} ({_task_count(repo_id)} tasks completed)"""

    client = instrumented_anthropic_client(role="confidence", task_id=task_id, api_key_id=api_key_id)
    try:
        resp = await client.messages.create(
            model=settings.confidence_model,
            max_tokens=256,
            system=_SYSTEM,
            messages=[{"role": "user", "content": context}],
        )
        raw = resp.content[0].text.strip()
        data = json.loads(raw)
        score = float(max(0, min(100, data.get("score", 50))))
        reasoning = str(data.get("reasoning", "")).strip()
        return score, reasoning
    except Exception as exc:
        _log.warning("Confidence scoring failed: %s", exc)
        words = len(description.split())
        score = min(75.0, 40.0 + words * 1.5)
        return score, "Confidence scoring unavailable -- estimated from task description length."


def _historical_success_rate(repo_id: str) -> float:
    with Session(engine) as session:
        total = session.exec(
            select(func.count(TaskMetrics.id)).where(TaskMetrics.repo_id == repo_id)
        ).one()
        if not total:
            return 0.5
        successes = session.exec(
            select(func.count(TaskMetrics.id)).where(
                TaskMetrics.repo_id == repo_id,
                TaskMetrics.success == True,
            )
        ).one()
        return successes / total


def _task_count(repo_id: str) -> int:
    with Session(engine) as session:
        return session.exec(
            select(func.count(TaskMetrics.id)).where(TaskMetrics.repo_id == repo_id)
        ).one() or 0
