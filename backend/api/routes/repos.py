from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select

from database import get_session
from models.task import Repo, Workspace, RepoStatus
from models.schemas import RepoCreate, RepoResponse, WorkspaceCreate, WorkspaceResponse

router = APIRouter(tags=["repos"])
ws_router = APIRouter(prefix="/workspaces", tags=["workspaces"])
repo_router = APIRouter(prefix="/repos", tags=["repos"])


@ws_router.post("/", response_model=WorkspaceResponse)
def create_workspace(body: WorkspaceCreate, session: Session = Depends(get_session)):
    workspace = Workspace(name=body.name, description=body.description)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace


@ws_router.get("/", response_model=list[WorkspaceResponse])
def list_workspaces(session: Session = Depends(get_session)):
    return session.exec(select(Workspace)).all()


@ws_router.get("/{workspace_id}/repos", response_model=list[RepoResponse])
def list_workspace_repos(workspace_id: str, session: Session = Depends(get_session)):
    return session.exec(select(Repo).where(Repo.workspace_id == workspace_id)).all()


@repo_router.post("/", response_model=RepoResponse)
def add_repo(body: RepoCreate, session: Session = Depends(get_session)):
    repo = Repo(workspace_id=body.workspace_id, url=body.url, name=body.name)
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo


@repo_router.get("/{repo_id}", response_model=RepoResponse)
def get_repo(repo_id: str, session: Session = Depends(get_session)):
    repo = session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    return repo
