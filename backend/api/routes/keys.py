from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select, func

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


@router.get("/usage")
async def get_usage(
    api_key: ApiKey = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    from models.token_usage import TokenUsage

    since = datetime.now(timezone.utc) - timedelta(days=30)
    rows = session.exec(
        select(
            TokenUsage.model,
            TokenUsage.role,
            func.sum(TokenUsage.input_tokens).label("input_tokens"),
            func.sum(TokenUsage.output_tokens).label("output_tokens"),
            func.sum(TokenUsage.cost_usd).label("cost_usd"),
        )
        .where(
            TokenUsage.api_key_id == api_key.id,
            TokenUsage.created_at >= since,
        )
        .group_by(TokenUsage.model, TokenUsage.role)
    ).all()

    breakdown = [
        {
            "model": r.model,
            "role": r.role,
            "input_tokens": r.input_tokens or 0,
            "output_tokens": r.output_tokens or 0,
            "cost_usd": round(r.cost_usd or 0.0, 6),
        }
        for r in rows
    ]

    total_cost = sum(r["cost_usd"] for r in breakdown)
    total_input = sum(r["input_tokens"] for r in breakdown)
    total_output = sum(r["output_tokens"] for r in breakdown)

    return {
        "period_days": 30,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_usd": round(total_cost, 6),
        "breakdown": breakdown,
    }


def _encrypt(value: str) -> str:
    from config import settings
    import base64, hashlib
    enc_key = settings.encryption_key
    if not enc_key:
        return value
    try:
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(hashlib.sha256(enc_key.encode()).digest())
        return Fernet(key).encrypt(value.encode()).decode()
    except Exception:
        return value


def _decrypt(value: str) -> str:
    from config import settings
    import base64, hashlib
    enc_key = settings.encryption_key
    if not enc_key:
        return value
    try:
        from cryptography.fernet import Fernet
        key = base64.urlsafe_b64encode(hashlib.sha256(enc_key.encode()).digest())
        return Fernet(key).decrypt(value.encode()).decode()
    except Exception:
        return value


class ByokRequest(BaseModel):
    anthropic_key: str = ""
    voyage_key: str = ""


@router.post("/byok")
async def set_byok(
    body: ByokRequest,
    api_key: ApiKey = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    record = session.get(ApiKey, api_key.id)
    if not record:
        raise HTTPException(status_code=404, detail="Key not found")
    if body.anthropic_key:
        record.user_anthropic_key_encrypted = _encrypt(body.anthropic_key)
    if body.voyage_key:
        record.user_voyage_key_encrypted = _encrypt(body.voyage_key)
    session.add(record)
    session.commit()
    return {"status": "byok keys stored", "anthropic": bool(body.anthropic_key), "voyage": bool(body.voyage_key)}


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
