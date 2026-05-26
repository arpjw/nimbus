from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class FileIndexState(SQLModel, table=True):
    id: str = Field(primary_key=True)
    repo_id: str = Field(index=True)
    file_path: str
    content_hash: str
    chunk_ids: str
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
