from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select

from database import get_session, engine
from models.health import HealthSnapshot
from api.routes.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/health-reports", tags=["health"])


@router.post("/{repo_id}/scan")
async def run_health_scan(
    repo_id: str,
    workspace_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(_run_scan, repo_id, workspace_id)
    return {"status": "scanning", "repo_id": repo_id}


async def _run_scan(repo_id: str, workspace_id: str):
    from services.health_scorer import generate_health_snapshot
    from pathlib import Path
    from sqlmodel import Session as SQLSession

    with SQLSession(engine) as db:
        previous = db.exec(
            select(HealthSnapshot)
            .where(HealthSnapshot.repo_id == repo_id)
            .order_by(HealthSnapshot.created_at.desc())
        ).first()

        repo_path = Path.cwd()

        try:
            data = await generate_health_snapshot(repo_id, workspace_id, repo_path, previous)
            snapshot = HealthSnapshot(**data)
            db.add(snapshot)
            db.commit()
        except Exception as e:
            print(f"Health scan failed: {e}")


@router.get("/{repo_id}")
async def get_health_report(
    repo_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    snapshot = session.exec(
        select(HealthSnapshot)
        .where(HealthSnapshot.repo_id == repo_id)
        .order_by(HealthSnapshot.created_at.desc())
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="No health report found. Run a scan first.")

    return snapshot


@router.get("/{repo_id}/history")
async def get_health_history(
    repo_id: str,
    limit: int = 12,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    snapshots = session.exec(
        select(HealthSnapshot)
        .where(HealthSnapshot.repo_id == repo_id)
        .order_by(HealthSnapshot.created_at.desc())
        .limit(limit)
    ).all()
    return snapshots
