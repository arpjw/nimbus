from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from services.auth import ApiKey, generate_api_key, require_api_key
from api.routes.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/keys", tags=["keys"])


class GenerateKeyRequest(BaseModel):
    name: str
    owner_email: str


@router.post("/generate")
async def generate_key(body: GenerateKeyRequest, session: Session = Depends(get_session)):
    raw_key, hashed_key = generate_api_key()
    api_key = ApiKey(
        key=hashed_key,
        name=body.name,
        owner_email=body.owner_email,
        created_at=datetime.now(timezone.utc),
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return {
        "id": api_key.id,
        "raw_key": raw_key,
        "name": api_key.name,
        "owner_email": api_key.owner_email,
        "tier": api_key.tier,
    }


@router.get("/current")
async def get_me(api_key: ApiKey = Depends(require_api_key)):
    from config import settings
    return {
        "id": api_key.id,
        "name": api_key.name,
        "owner_email": api_key.owner_email,
        "tier": api_key.tier,
        "task_count_month": api_key.task_count_month,
        "monthly_limit": settings.free_tier_monthly_limit if api_key.tier == "free" else None,
        "last_used_at": api_key.last_used_at,
    }


@router.get("/me")
async def get_my_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    keys = session.exec(select(ApiKey).where(ApiKey.user_id == current_user.id)).all()
    return [{"id": k.id, "name": k.name, "key_preview": k.key[:8] + "...", "created_at": k.created_at} for k in keys]


@router.delete("/{key_id}")
async def delete_key(
    key_id: str,
    api_key: ApiKey = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    if api_key.id != key_id:
        raise HTTPException(status_code=403, detail="Cannot delete another key")
    record = session.get(ApiKey, key_id)
    if not record:
        raise HTTPException(status_code=404, detail="Key not found")
    session.delete(record)
    session.commit()
    return {"deleted": key_id}
