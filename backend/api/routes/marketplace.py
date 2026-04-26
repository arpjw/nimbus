from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from database import get_session
from api.routes.auth import get_current_user
from models.skill import Skill
from models.user import User

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("/skills")
async def list_marketplace_skills(
    q: Optional[str] = Query(None, description="Search query"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    sort: str = Query("popular", description="popular|recent|name"),
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
):
    query = select(Skill).where(Skill.is_public == True)  # noqa: E712

    if q:
        query = query.where(
            (Skill.name.contains(q)) | (Skill.description.contains(q))
        )
    if tags:
        for tag in tags.split(","):
            query = query.where(Skill.tags.contains(tag.strip()))

    skills = session.exec(query.limit(limit)).all()
    return [
        {
            "name": s.name,
            "description": s.description,
            "prompt": s.system_prompt_addition,
            "tags": s.tags,
            "install_count": s.install_count,
            "star_count": s.star_count,
            "author_username": s.author_username,
            "version": s.version,
        }
        for s in skills
    ]


@router.post("/skills/{skill_name}/install")
async def install_skill(
    skill_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    skill = session.exec(
        select(Skill).where(Skill.name == skill_name, Skill.is_public == True)  # noqa: E712
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found in marketplace")

    skill.install_count = (skill.install_count or 0) + 1
    session.add(skill)
    session.commit()
    session.refresh(skill)

    return {
        "name": skill.name,
        "description": skill.description,
        "prompt": skill.system_prompt_addition,
        "install_count": skill.install_count,
    }


@router.post("/skills/{skill_name}/star")
async def star_skill(
    skill_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    skill = session.exec(
        select(Skill).where(Skill.name == skill_name, Skill.is_public == True)  # noqa: E712
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill.star_count = (skill.star_count or 0) + 1
    session.add(skill)
    session.commit()
    return {"star_count": skill.star_count}


class PublishSkillRequest(BaseModel):
    name: str
    description: str
    prompt: str
    tags: Optional[str] = None
    version: str = "1.0.0"


@router.post("/skills/publish")
async def publish_skill(
    body: PublishSkillRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing = session.exec(
        select(Skill).where(Skill.name == body.name, Skill.is_public == True)  # noqa: E712
    ).first()
    if existing and existing.author_id != current_user.id:
        raise HTTPException(status_code=409, detail=f"Skill name '{body.name}' already taken")

    skill = Skill(
        name=body.name,
        description=body.description,
        system_prompt_addition=body.prompt,
        tags=body.tags,
        version=body.version,
        is_public=True,
        author_id=current_user.id,
        author_username=current_user.github_username,
    )
    session.add(skill)
    session.commit()
    session.refresh(skill)
    return {
        "name": skill.name,
        "description": skill.description,
        "prompt": skill.system_prompt_addition,
        "tags": skill.tags,
        "version": skill.version,
        "install_count": skill.install_count,
        "star_count": skill.star_count,
        "author_username": skill.author_username,
    }
