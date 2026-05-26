from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class TokenUsage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    task_id: Optional[str] = Field(default=None, index=True)
    api_key_id: Optional[str] = Field(default=None, index=True)
    provider: str
    model: str
    role: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
