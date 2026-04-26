import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlmodel import Field, Session, SQLModel, select

from database import get_session


class ApiKey(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    key: str = Field(unique=True, index=True)
    name: str
    owner_email: str = Field(default="")
    tier: str = "free"
    task_count_month: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
    user_id: Optional[str] = Field(default=None, foreign_key="user.id")


def generate_api_key() -> tuple[str, str]:
    raw_key = "nk_" + secrets.token_urlsafe(32)
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, hashed_key


async def get_api_key(key: str, session: Session) -> Optional[ApiKey]:
    hashed = hashlib.sha256(key.encode()).hexdigest()
    return session.exec(select(ApiKey).where(ApiKey.key == hashed)).first()


async def require_api_key(
    x_api_key: Optional[str] = Header(None),
    session: Session = Depends(get_session),
) -> ApiKey:
    from config import settings

    if not settings.require_api_key:
        return ApiKey(
            id="local",
            key="",
            name="local",
            owner_email="local",
            tier="pro",
            created_at=datetime.now(timezone.utc),
        )

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    api_key = await get_api_key(x_api_key, session)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


async def check_rate_limit(api_key: ApiKey) -> None:
    from config import settings

    if api_key.tier == "free" and api_key.task_count_month >= settings.free_tier_monthly_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Free tier limit of {settings.free_tier_monthly_limit} tasks/month reached",
        )
