from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class TaskMetrics(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    task_id: str = Field(index=True)
    workspace_id: str = Field(index=True)
    repo_id: Optional[str] = None

    task_type: str = Field(default="implementation")
    agent_name: Optional[str] = None

    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    success: bool = Field(default=False)
    pr_opened: bool = Field(default=False)
    tests_passed: bool = Field(default=False)

    estimated_cost_usd: Optional[float] = None

    review_score: Optional[float] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
