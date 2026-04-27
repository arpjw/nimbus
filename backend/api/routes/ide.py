from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_session
from models.ide_session import IDESession
from api.routes.auth import get_current_user
from models.user import User
import os

router = APIRouter(prefix="/ide", tags=["ide"])


class CreateSessionRequest(BaseModel):
    repo: Optional[str] = None      # owner/name — clone this repo on startup
    branch: str = "main"


class SessionResponse(BaseModel):
    id: str
    status: str
    machine_url: Optional[str]
    repo: Optional[str]
    branch: str
    created_at: datetime


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    body: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new IDE session — spins up a Fly Machine."""
    session = IDESession(
        user_id=current_user.id,
        repo=body.repo,
        branch=body.branch,
        status="starting",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    background_tasks.add_task(_start_machine, session.id, current_user.id)

    return SessionResponse(
        id=session.id,
        status=session.status,
        machine_url=session.fly_machine_url,
        repo=session.repo,
        branch=session.branch,
        created_at=session.created_at,
    )


async def _start_machine(session_id: str, user_id: str):
    """Background task: create Fly Machine and update session record."""
    from database import engine
    from sqlmodel import Session as SQLSession
    from services.fly_machines import create_machine, wait_for_machine_ready

    with SQLSession(engine) as db:
        session = db.get(IDESession, session_id)
        if not session:
            return

        try:
            machine = await create_machine(session_id=session_id)
            machine_id = machine.get("id")

            session.fly_machine_id = machine_id
            db.add(session)
            db.commit()

            ready = await wait_for_machine_ready(machine_id, timeout=30)

            if ready:
                app_name = os.environ.get("FLY_APP_NAME", "nimbus-ide")
                session.fly_machine_url = f"https://{app_name}.fly.dev"
                session.status = "ready"
            else:
                session.status = "error"

            db.add(session)
            db.commit()

        except Exception as e:
            session.status = "error"
            db.add(session)
            db.commit()
            print(f"Failed to start IDE machine for session {session_id}: {e}")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get the status of an IDE session."""
    session = db.get(IDESession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    session.last_active_at = datetime.utcnow()
    db.add(session)
    db.commit()

    return SessionResponse(
        id=session.id,
        status=session.status,
        machine_url=session.fly_machine_url,
        repo=session.repo,
        branch=session.branch,
        created_at=session.created_at,
    )


@router.delete("/sessions/{session_id}")
async def stop_session(
    session_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Stop and destroy an IDE session."""
    session = db.get(IDESession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    if session.fly_machine_id:
        try:
            from services.fly_machines import stop_machine
            await stop_machine(session.fly_machine_id)
        except Exception as e:
            print(f"Warning: failed to stop machine {session.fly_machine_id}: {e}")

    session.status = "stopped"
    session.stopped_at = datetime.utcnow()
    db.add(session)
    db.commit()

    return {"status": "stopped", "session_id": session_id}


@router.get("/sessions")
async def list_sessions(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List active IDE sessions for the current user."""
    sessions = db.exec(
        select(IDESession)
        .where(IDESession.user_id == current_user.id)
        .where(IDESession.status != "stopped")
        .order_by(IDESession.created_at.desc())
        .limit(5)
    ).all()
    return sessions
