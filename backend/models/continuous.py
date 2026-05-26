from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from sqlmodel import Field, SQLModel


class ContinuousSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    api_key_id: str = Field(index=True)
    repo_id: str = Field(index=True)
    daily_spend_cap_usd: float
    label_filter: Optional[str] = None
    confidence_threshold: int = 70
    status: str = Field(default="active")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    total_spent_usd: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_checked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
