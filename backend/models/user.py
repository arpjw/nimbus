from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    github_id: str = Field(unique=True, index=True)
    github_username: str
    github_email: Optional[str] = None
    github_avatar_url: Optional[str] = None
    plan: str = Field(default="free")
    tasks_this_month: int = Field(default=0)
    tasks_month_reset: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
