from __future__ import annotations

from typing import Optional

from sqlmodel import Session

from database import engine
from services.auth import get_api_key
from models.task import Workspace


async def resolve_api_key(raw_key: Optional[str]):
    if not raw_key:
        return None
    with Session(engine) as session:
        return await get_api_key(raw_key, session)
