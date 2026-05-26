from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

_GONE = HTTPException(
    status_code=410,
    detail="The skill marketplace is paused. Built-in agents are still available via `nimbus agents`.",
)


@router.get("/skills")
async def list_marketplace_skills():
    raise _GONE


@router.post("/skills/{skill_name}/install")
async def install_skill(skill_name: str):
    raise _GONE


@router.post("/skills/{skill_name}/star")
async def star_skill(skill_name: str):
    raise _GONE


@router.post("/skills/publish")
async def publish_skill():
    raise _GONE
