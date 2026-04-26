from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field
import uuid


class Phase(str, Enum):
    QUEUED = "queued"
    CLONING = "cloning"
    INDEXING = "indexing"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    AWAITING_DIFF_APPROVAL = "awaiting_diff_approval"
    IMPLEMENTING = "implementing"
    VERIFYING = "verifying"
    FIXING = "fixing"
    REVIEWING = "reviewing"
    PR_CREATION = "pr_creation"
    CLEANUP = "cleanup"
    DONE = "done"
    FAILED = "failed"


class RepoStatus(str, Enum):
    PENDING = "pending"
    INDEXED = "indexed"
    ERROR = "error"


class Repo(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    url: str
    workspace_id: str
    status: RepoStatus = RepoStatus.PENDING
    indexed_at: Optional[datetime] = None
    file_count: int = 0
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Workspace(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    workspace_id: str
    repo_id: str
    description: str
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    phase: Phase = Phase.QUEUED
    iteration: int = 0
    error: Optional[str] = None
    plan: Optional[str] = None
    issue_number: Optional[int] = None
    repo_full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ChannelRepoMap(SQLModel, table=True):
    channel_id: str = Field(primary_key=True)
    repo_url: str
    workspace_id: str


class LinearTeamRepoMap(SQLModel, table=True):
    linear_team_id: str = Field(primary_key=True)
    github_repo_url: str
    workspace_id: str
