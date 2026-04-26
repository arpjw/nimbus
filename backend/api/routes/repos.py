from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models.task import Repo, Workspace, RepoStatus
from models.schemas import RepoCreate, RepoResponse, WorkspaceCreate, WorkspaceResponse
from services.memory import list_repo_memory, delete_repo_memory, add_manual_repo_memory

router = APIRouter(tags=["repos"])
ws_router = APIRouter(prefix="/workspaces", tags=["workspaces"])
repo_router = APIRouter(prefix="/repos", tags=["repos"])


class ManualMemoryCreate(BaseModel):
    text: str
    label: str = ""


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


@repo_router.get("/", response_model=list[RepoResponse])
def list_repos(session: Session = Depends(get_session)):
    return session.exec(select(Repo)).all()


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


@repo_router.get("/{repo_id}/memory")
async def list_memory(repo_id: str, session: Session = Depends(get_session)):
    repo = session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    return await list_repo_memory(repo_id)


@repo_router.post("/{repo_id}/memory")
async def add_memory(repo_id: str, body: ManualMemoryCreate, session: Session = Depends(get_session)):
    repo = session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    return await add_manual_repo_memory(repo_id, body.text, body.label)


@repo_router.delete("/{repo_id}/memory/{memory_id}")
async def delete_memory(repo_id: str, memory_id: str, session: Session = Depends(get_session)):
    repo = session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    found = await delete_repo_memory(repo_id, memory_id)
    if not found:
        raise HTTPException(status_code=404, detail="Memory entry not found")
    return {"deleted": memory_id}
