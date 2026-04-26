from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models.task import LinearTeamRepoMap

router = APIRouter(prefix="/linear", tags=["linear"])


class TeamMappingCreate(BaseModel):
    linear_team_id: str
    github_repo_url: str
    workspace_id: str


@router.post("/teams", response_model=TeamMappingCreate)
def register_team(body: TeamMappingCreate, session: Session = Depends(get_session)):
    existing = session.get(LinearTeamRepoMap, body.linear_team_id)
    if existing:
        raise HTTPException(status_code=409, detail="Team mapping already exists")

    mapping = LinearTeamRepoMap(
        linear_team_id=body.linear_team_id,
        github_repo_url=body.github_repo_url,
        workspace_id=body.workspace_id,
    )
    session.add(mapping)
    session.commit()
    return mapping


@router.get("/teams", response_model=list[TeamMappingCreate])
def list_teams(session: Session = Depends(get_session)):
    return session.exec(select(LinearTeamRepoMap)).all()
