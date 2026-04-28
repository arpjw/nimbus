from fastapi import APIRouter, HTTPException, BackgroundTasks, Header, Depends
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_session
from models.ide_session import IDESession
import os

router = APIRouter(prefix="/ide", tags=["ide"])

NIMBUS_API_URL = os.environ.get("NIMBUS_API_URL", "https://api.get-nimbus.com")


async def verify_api_key(x_api_key: Optional[str] = None, authorization: Optional[str] = None) -> str:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    elif x_api_key:
        token = x_api_key

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Accept any nk_ key — format check only, no DB lookup
    if token.startswith("nk_") and len(token) > 10:
        return token  # use the key itself as the user identifier

    # Try JWT decode for browser sessions
    try:
        from api.routes.auth import decode_nimbus_token
        return decode_nimbus_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


class CreateSessionRequest(BaseModel):
    repo: Optional[str] = None
    branch: str = "main"


@router.post("/sessions")
async def create_session(
    body: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    user_id = await verify_api_key(x_api_key, authorization)

    session = IDESession(
        user_id=user_id,
        repo=body.repo,
        branch=body.branch,
        status="starting",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    background_tasks.add_task(_start_machine, session.id, user_id)

    return {
        "id": session.id,
        "status": session.status,
        "machine_url": session.fly_machine_url,
        "repo": session.repo,
        "branch": session.branch,
        "created_at": session.created_at,
    }


@router.get("/sessions/{session_id}")
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_session),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    await verify_api_key(x_api_key, authorization)
    session = db.get(IDESession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.last_active_at = datetime.utcnow()
    db.add(session)
    db.commit()
    return {
        "id": session.id,
        "status": session.status,
        "machine_url": session.fly_machine_url,
        "repo": session.repo,
        "branch": session.branch,
        "created_at": session.created_at,
    }


@router.delete("/sessions/{session_id}")
async def stop_session(
    session_id: str,
    db: Session = Depends(get_session),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    await verify_api_key(x_api_key, authorization)
    session = db.get(IDESession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.fly_machine_id:
        try:
            from services.fly_machines import stop_machine
            await stop_machine(session.fly_machine_id)
        except Exception as e:
            print(f"Warning: failed to stop machine: {e}")
    session.status = "stopped"
    session.stopped_at = datetime.utcnow()
    db.add(session)
    db.commit()
    return {"status": "stopped", "session_id": session_id}


@router.get("/sessions")
async def list_sessions(
    db: Session = Depends(get_session),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    user_id = await verify_api_key(x_api_key, authorization)
    sessions = db.exec(
        select(IDESession)
        .where(IDESession.user_id == user_id)
        .where(IDESession.status != "stopped")
        .order_by(IDESession.created_at.desc())
        .limit(5)
    ).all()
    return sessions


async def _start_machine(session_id: str, user_id: str):
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
            app_name = os.environ.get("FLY_APP_NAME", "nimbus-ide")

            if ready:
                session.fly_machine_url = f"https://{app_name}.fly.dev"
                session.status = "ready"
            else:
                session.status = "error"

            db.add(session)
            db.commit()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Machine start failed: {e}")
            session.status = "error"
            db.add(session)
            db.commit()
