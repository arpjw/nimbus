from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class IDESession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    fly_machine_id: Optional[str] = None
    fly_machine_url: Optional[str] = None
    repo: Optional[str] = None          # owner/name
    branch: str = Field(default="main")
    status: str = Field(default="starting")  # starting | ready | stopped | error
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    stopped_at: Optional[datetime] = None
