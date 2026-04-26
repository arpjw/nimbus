from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from database import get_session
from models.schemas import TaskResponse
from services.agent_library import list_agents, get_agent, CATEGORIES
from services.auth import ApiKey, require_api_key
from api.routes.tasks import create_task_internal

router = APIRouter(prefix="/agents", tags=["agents"])


class RunAgentRequest(BaseModel):
    workspace_id: str
    repo_id: str
    dry_run: bool = False


@router.get("/")
async def list_all_agents(category: str = None, api_key: ApiKey = Depends(require_api_key)):
    agents = list_agents(category)
    return [{
        "name": a.name,
        "category": a.category,
        "description": a.description,
        "estimated_prs": a.estimated_prs,
        "dry_run_safe": a.dry_run_safe,
    } for a in agents]


@router.get("/categories")
async def get_categories(api_key: ApiKey = Depends(require_api_key)):
    return {"categories": CATEGORIES}


@router.get("/{name}")
async def get_agent_info(name: str, api_key: ApiKey = Depends(require_api_key)):
    agent = get_agent(name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return {
        "name": agent.name,
        "category": agent.category,
        "description": agent.description,
        "full_description": agent.full_description,
        "retrieval_strategy": agent.retrieval_strategy,
        "verification_command": agent.verification_command,
        "estimated_prs": agent.estimated_prs,
        "dry_run_safe": agent.dry_run_safe,
    }


@router.post("/{name}/run", response_model=TaskResponse)
async def run_agent(
    name: str,
    body: RunAgentRequest,
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_key),
):
    agent = get_agent(name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    if body.dry_run and not agent.dry_run_safe:
        raise HTTPException(status_code=400, detail=f"Agent '{name}' is not dry-run safe")

    task_description = agent.full_description
    if body.dry_run:
        task_description = f"[DRY RUN - show plan only, do not make changes] {task_description}"

    task = await create_task_internal(
        workspace_id=body.workspace_id,
        repo_id=body.repo_id,
        description=task_description,
        session=session,
        api_key=api_key,
    )
    return task
