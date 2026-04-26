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
    is_public: bool = Field(default=False)
    author_id: Optional[str] = Field(default=None, foreign_key="user.id")
    author_username: Optional[str] = None
    tags: Optional[str] = None
    install_count: int = Field(default=0)
    star_count: int = Field(default=0)
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
