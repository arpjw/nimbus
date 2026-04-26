from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session
from typing import Optional

from database import get_session
from prism.parser import parse_spec_to_tasks, topological_sort
from services.auth import ApiKey, require_api_key
from api.routes.tasks import nimbus_client_for_key

router = APIRouter(prefix="/prism", tags=["prism"])


class ParseRequest(BaseModel):
    spec: str


class PrismTask(BaseModel):
    id: int
    description: str
    skill: Optional[str] = None
    depends_on: list[int] = []
    priority: int = 1


class QueueRequest(BaseModel):
    tasks: list[PrismTask]
    repo_id: str
    workspace_id: str


async def submit_nimbus_task(
    workspace_id: str,
    repo_id: str,
    description: str,
    skill: str | None,
    session: Session,
    api_key: ApiKey,
) -> dict:
    task = await nimbus_client_for_key(
        workspace_id=workspace_id,
        repo_id=repo_id,
        description=description,
        session=session,
        api_key=api_key,
        skill=skill,
    )
    return {"id": task.id}


@router.post("/parse")
async def parse_spec(
    body: ParseRequest,
    api_key: ApiKey = Depends(require_api_key),
):
    tasks = await parse_spec_to_tasks(body.spec)
    return {"tasks": tasks}


@router.post("/queue")
async def queue_tasks(
    body: QueueRequest,
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_key),
):
    ordered = topological_sort([t.dict() for t in body.tasks])
    queued = []
    for task in ordered:
        result = await submit_nimbus_task(
            workspace_id=body.workspace_id,
            repo_id=body.repo_id,
            description=task["description"],
            skill=task.get("skill"),
            session=session,
            api_key=api_key,
        )
        queued.append({"task_id": result["id"], "prism_id": task["id"], "description": task["description"]})
    return {"queued": queued}
