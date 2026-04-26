from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid


class Skill(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True)
    owner_key_id: Optional[str] = Field(default=None, index=True)
    description: str
    system_prompt_addition: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
