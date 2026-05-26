from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import engine
from models.continuous import ContinuousSession
from models.task import Repo, Task
from models.token_usage import TokenUsage
from services.auth import require_api_key, ApiKey

router = APIRouter(prefix="/continuous", tags=["continuous"])


class StartSessionRequest(BaseModel):
    repo_id: str
    daily_spend_cap_usd: float
    duration_days: int = 30
    label_filter: Optional[str] = None
    confidence_threshold: int = 70


@router.post("/sessions", response_model=dict)
async def start_session(
    req: StartSessionRequest,
    api_key: ApiKey = Depends(require_api_key),
):
    with Session(engine) as session:
        repo = session.get(Repo, req.repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repo not found")

        cs = ContinuousSession(
            api_key_id=api_key.id,
            repo_id=req.repo_id,
            daily_spend_cap_usd=req.daily_spend_cap_usd,
            label_filter=req.label_filter,
            confidence_threshold=req.confidence_threshold,
            expires_at=datetime.utcnow() + timedelta(days=req.duration_days),
        )
        session.add(cs)
        session.commit()
        session.refresh(cs)
        return _session_dict(cs)


@router.get("/sessions", response_model=list)
async def list_sessions(api_key: ApiKey = Depends(require_api_key)):
    with Session(engine) as session:
        sessions = session.exec(
            select(ContinuousSession).where(ContinuousSession.api_key_id == api_key.id)
        ).all()
        return [_session_dict(s) for s in sessions]


@router.post("/sessions/{session_id}/pause", response_model=dict)
async def pause_session(session_id: str, api_key: ApiKey = Depends(require_api_key)):
    return _set_status(session_id, api_key.id, "paused")


@router.post("/sessions/{session_id}/resume", response_model=dict)
async def resume_session(session_id: str, api_key: ApiKey = Depends(require_api_key)):
    return _set_status(session_id, api_key.id, "active")


@router.post("/sessions/{session_id}/stop", response_model=dict)
async def stop_session(session_id: str, api_key: ApiKey = Depends(require_api_key)):
    return _set_status(session_id, api_key.id, "stopped")


@router.get("/sessions/{session_id}/activity", response_model=list)
async def session_activity(session_id: str, api_key: ApiKey = Depends(require_api_key)):
    with Session(engine) as session:
        cs = _get_owned(session_id, api_key.id)
        tasks = session.exec(
            select(Task).where(
                Task.repo_id == cs.repo_id,
                Task.created_at >= cs.started_at,
            ).order_by(Task.created_at.desc()).limit(100)
        ).all()
        return [
            {
                "task_id": t.id,
                "description": t.description[:100],
                "phase": t.phase.value,
                "pr_url": t.pr_url,
                "confidence": t.confidence_score,
                "cost": _task_cost(t.id),
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]


def _get_owned(session_id: str, api_key_id: str) -> ContinuousSession:
    with Session(engine) as session:
        cs = session.get(ContinuousSession, session_id)
        if not cs or cs.api_key_id != api_key_id:
            raise HTTPException(status_code=404, detail="Session not found")
        return cs


def _set_status(session_id: str, api_key_id: str, status: str) -> dict:
    with Session(engine) as session:
        cs = session.get(ContinuousSession, session_id)
        if not cs or cs.api_key_id != api_key_id:
            raise HTTPException(status_code=404, detail="Session not found")
        cs.status = status
        cs.updated_at = datetime.utcnow()
        session.add(cs)
        session.commit()
        session.refresh(cs)
        return _session_dict(cs)


def _session_dict(cs: ContinuousSession) -> dict:
    return {
        "id": cs.id,
        "repo_id": cs.repo_id,
        "status": cs.status,
        "daily_spend_cap_usd": cs.daily_spend_cap_usd,
        "label_filter": cs.label_filter,
        "confidence_threshold": cs.confidence_threshold,
        "started_at": cs.started_at.isoformat(),
        "expires_at": cs.expires_at.isoformat(),
        "total_spent_usd": cs.total_spent_usd,
        "tasks_completed": cs.tasks_completed,
        "tasks_failed": cs.tasks_failed,
    }


def _task_cost(task_id: str) -> float:
    from sqlmodel import func
    with Session(engine) as session:
        total = session.exec(
            select(func.sum(TokenUsage.cost_usd)).where(TokenUsage.task_id == task_id)
        ).one()
        return float(total or 0)
