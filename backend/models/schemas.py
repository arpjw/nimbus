from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from models.task import Phase, RepoStatus


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime


class RepoCreate(BaseModel):
    workspace_id: str
    url: str
    name: str


class RepoResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    url: str
    status: RepoStatus
    file_count: int
    chunk_count: int
    indexed_at: Optional[datetime]
    created_at: datetime


class TaskCreate(BaseModel):
    workspace_id: str
    repo_id: str
    description: str
    issue_number: Optional[int] = None
    repo_full_name: Optional[str] = None
    skill: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    repo_id: str
    description: str
    phase: Phase
    iteration: int
    branch_name: Optional[str]
    pr_url: Optional[str]
    error: Optional[str]
    plan: Optional[str]
    repo_full_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]


class WSEvent(BaseModel):
    task_id: str
    phase: Phase
    message: str
    timestamp: datetime = datetime.utcnow()
    data: Optional[dict] = None
