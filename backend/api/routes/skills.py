from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models.skill import Skill
from services.skills import SkillsService
from services.auth import ApiKey, require_api_key

router = APIRouter(prefix="/skills", tags=["skills"])

_skills_service = SkillsService()


class SkillCreate(BaseModel):
    name: str
    description: str
    system_prompt_addition: str


@router.get("/", response_model=list[Skill])
async def list_skills(api_key: ApiKey = Depends(require_api_key)):
    return _skills_service.list_skills(api_key.id)


@router.post("/", response_model=Skill)
async def create_skill(body: SkillCreate, api_key: ApiKey = Depends(require_api_key)):
    return _skills_service.create_skill(
        api_key.id, body.name, body.description, body.system_prompt_addition
    )


@router.delete("/{name}")
async def delete_skill(
    name: str,
    api_key: ApiKey = Depends(require_api_key),
    session: Session = Depends(get_session),
):
    skill = session.exec(
        select(Skill).where(Skill.name == name, Skill.owner_key_id == api_key.id)
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found or not owned by you")
    _skills_service.delete_skill(skill.id, api_key.id)
    return {"status": "deleted"}
