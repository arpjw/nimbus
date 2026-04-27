from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class HealthSnapshot(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    repo_id: str = Field(index=True)
    workspace_id: str = Field(index=True)

    test_coverage: Optional[float] = None
    tech_debt_score: Optional[float] = None
    security_score: Optional[float] = None
    doc_coverage: Optional[float] = None
    dep_freshness: Optional[float] = None
    ci_pass_rate: Optional[float] = None
    overall_score: Optional[float] = None
    overall_grade: Optional[str] = None

    test_coverage_delta: Optional[float] = None
    tech_debt_delta: Optional[float] = None
    overall_delta: Optional[float] = None

    raw_metrics: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
