from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid


class Automation(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    owner_key_id: str
    repo_id: str
    task_template: str
    trigger_type: str
    trigger_config: str
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    last_task_id: Optional[str] = None
