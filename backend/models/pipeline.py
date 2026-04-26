from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class Pipeline(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    description: Optional[str] = None
    config: str
    schedule: Optional[str] = None
    enabled: bool = Field(default=True)
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineRun(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    pipeline_id: str = Field(foreign_key="pipeline.id", index=True)
    status: str = Field(default="running")
    steps_completed: int = Field(default=0)
    steps_total: int = Field(default=0)
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
