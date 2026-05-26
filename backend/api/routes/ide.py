from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models.ide_session import IDESession
from services.auth import ApiKey

router = APIRouter(prefix="/ide", tags=["ide"])

_FREE_CONCURRENT_LIMIT = 1
_PRO_CONCURRENT_LIMIT = 3
_FREE_MONTHLY_LIMIT = 5


async def _verify_api_key(
    x_api_key: Optional[str],
    authorization: Optional[str],
    db: Session,
) -> ApiKey:
    token: Optional[str] = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    elif x_api_key:
        token = x_api_key

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if token.startswith("nk_"):
        hashed = hashlib.sha256(token.encode()).hexdigest()
        api_key = db.exec(select(ApiKey).where(ApiKey.key == hashed)).first()
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return api_key

    try:
        from api.routes.auth import decode_nimbus_token
        user_id = decode_nimbus_token(token)
        api_key = db.exec(select(ApiKey).where(ApiKey.user_id == user_id)).first()
        if api_key:
            return api_key
        raise HTTPException(status_code=401, detail="No API key associated with this account")
    except HTTPException:
        raise
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
    api_key = await _verify_api_key(x_api_key, authorization, db)
    user_id = api_key.user_id or api_key.id

    concurrent_limit = _PRO_CONCURRENT_LIMIT if api_key.tier == "pro" else _FREE_CONCURRENT_LIMIT
    active_sessions = db.exec(
        select(IDESession)
        .where(IDESession.user_id == user_id)
        .where(IDESession.status.in_(["starting", "ready"]))
    ).all()
    if len(active_sessions) >= concurrent_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Concurrent session limit of {concurrent_limit} reached for {api_key.tier} tier",
        )

    if api_key.tier != "pro":
        if api_key.ide_session_count_month >= _FREE_MONTHLY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly IDE session limit of {_FREE_MONTHLY_LIMIT} reached",
            )

    ide_session = IDESession(
        user_id=user_id,
        repo=body.repo,
        branch=body.branch,
        status="starting",
    )
    db.add(ide_session)

    if api_key.tier != "pro" and api_key.id not in ("local", user_id):
        db_key = db.get(ApiKey, api_key.id)
        if db_key:
            db_key.ide_session_count_month += 1
            db.add(db_key)

    db.commit()
    db.refresh(ide_session)

    background_tasks.add_task(_start_machine, ide_session.id, user_id)

    return {
        "id": ide_session.id,
        "status": ide_session.status,
        "machine_url": ide_session.fly_machine_url,
        "repo": ide_session.repo,
        "branch": ide_session.branch,
        "created_at": ide_session.created_at,
    }


@router.get("/sessions/{session_id}")
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_session),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    await _verify_api_key(x_api_key, authorization, db)
    ide_session = db.get(IDESession, session_id)
    if not ide_session:
        raise HTTPException(status_code=404, detail="Session not found")
    ide_session.last_active_at = datetime.utcnow()
    db.add(ide_session)
    db.commit()
    return {
        "id": ide_session.id,
        "status": ide_session.status,
        "machine_url": ide_session.fly_machine_url,
        "repo": ide_session.repo,
        "branch": ide_session.branch,
        "created_at": ide_session.created_at,
    }


@router.delete("/sessions/{session_id}")
async def stop_session(
    session_id: str,
    db: Session = Depends(get_session),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    await _verify_api_key(x_api_key, authorization, db)
    ide_session = db.get(IDESession, session_id)
    if not ide_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if ide_session.fly_machine_id:
        try:
            from services.fly_machines import stop_machine
            await stop_machine(ide_session.fly_machine_id)
        except Exception:
            pass
    ide_session.status = "stopped"
    ide_session.stopped_at = datetime.utcnow()
    db.add(ide_session)
    db.commit()
    return {"status": "stopped", "session_id": session_id}


@router.get("/sessions")
async def list_sessions(
    db: Session = Depends(get_session),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    api_key = await _verify_api_key(x_api_key, authorization, db)
    user_id = api_key.user_id or api_key.id
    sessions = db.exec(
        select(IDESession)
        .where(IDESession.user_id == user_id)
        .where(IDESession.status != "stopped")
        .order_by(IDESession.created_at.desc())
        .limit(5)
    ).all()
    return sessions


async def _start_machine(session_id: str, user_id: str) -> None:
    import os

    from database import engine
    from sqlmodel import Session as SQLSession
    from services.fly_machines import create_machine, wait_for_machine_ready

    with SQLSession(engine) as db:
        ide_session = db.get(IDESession, session_id)
        if not ide_session:
            return
        try:
            machine = await create_machine(session_id=session_id)
            machine_id = machine.get("id")
            ide_session.fly_machine_id = machine_id
            db.add(ide_session)
            db.commit()

            ready = await wait_for_machine_ready(machine_id, timeout=30)
            app_name = os.environ.get("FLY_APP_NAME", "nimbus-ide")

            if ready:
                ide_session.fly_machine_url = f"https://{app_name}.fly.dev"
                ide_session.status = "ready"
            else:
                ide_session.status = "error"

            db.add(ide_session)
            db.commit()
        except Exception:
            ide_session.status = "error"
            db.add(ide_session)
            db.commit()
