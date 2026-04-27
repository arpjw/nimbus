from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime, timedelta
from database import get_session
from models.task_metrics import TaskMetrics
from api.routes.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/velocity")
async def get_velocity(
    workspace_id: str,
    period_days: int = Query(30, description="Period in days (7, 30, 90)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(days=period_days)
    prev_since = since - timedelta(days=period_days)

    current = session.exec(
        select(TaskMetrics)
        .where(TaskMetrics.workspace_id == workspace_id)
        .where(TaskMetrics.created_at >= since)
    ).all()

    previous = session.exec(
        select(TaskMetrics)
        .where(TaskMetrics.workspace_id == workspace_id)
        .where(TaskMetrics.created_at >= prev_since)
        .where(TaskMetrics.created_at < since)
    ).all()

    def compute_stats(tasks):
        if not tasks:
            return {
                "total_tasks": 0,
                "success_rate": 0,
                "prs_opened": 0,
                "avg_duration_minutes": 0,
                "estimated_hours_saved": 0,
                "estimated_cost_usd": 0,
                "by_type": {},
            }
        total = len(tasks)
        successful = [t for t in tasks if t.success]
        prs = [t for t in tasks if t.pr_opened]
        durations = [t.duration_seconds for t in tasks if t.duration_seconds]
        avg_dur = sum(durations) / len(durations) if durations else 0
        hours_saved = len(successful) * 0.75
        cost = sum(t.estimated_cost_usd or 0.15 for t in tasks)

        by_type: dict[str, int] = {}
        for t in tasks:
            key = t.agent_name or t.task_type
            by_type[key] = by_type.get(key, 0) + 1

        return {
            "total_tasks": total,
            "success_rate": round(len(successful) / total * 100, 1) if total else 0,
            "prs_opened": len(prs),
            "avg_duration_minutes": round(avg_dur / 60, 1),
            "estimated_hours_saved": round(hours_saved, 1),
            "estimated_cost_usd": round(cost, 2),
            "by_type": by_type,
        }

    curr_stats = compute_stats(current)
    prev_stats = compute_stats(previous)

    def delta(curr, prev):
        if prev == 0:
            return None
        return round(curr - prev, 1)

    return {
        "period_days": period_days,
        "current": curr_stats,
        "previous": prev_stats,
        "deltas": {
            "total_tasks": delta(curr_stats["total_tasks"], prev_stats["total_tasks"]),
            "success_rate": delta(curr_stats["success_rate"], prev_stats["success_rate"]),
            "prs_opened": delta(curr_stats["prs_opened"], prev_stats["prs_opened"]),
            "hours_saved": delta(curr_stats["estimated_hours_saved"], prev_stats["estimated_hours_saved"]),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/velocity/timeline")
async def get_velocity_timeline(
    workspace_id: str,
    period_days: int = Query(30),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(days=period_days)
    tasks = session.exec(
        select(TaskMetrics)
        .where(TaskMetrics.workspace_id == workspace_id)
        .where(TaskMetrics.created_at >= since)
        .order_by(TaskMetrics.created_at)
    ).all()

    by_day: dict[str, dict] = {}
    for t in tasks:
        day = t.created_at.strftime("%Y-%m-%d")
        if day not in by_day:
            by_day[day] = {"date": day, "total": 0, "successful": 0, "prs": 0}
        by_day[day]["total"] += 1
        if t.success:
            by_day[day]["successful"] += 1
        if t.pr_opened:
            by_day[day]["prs"] += 1

    return sorted(by_day.values(), key=lambda x: x["date"])
