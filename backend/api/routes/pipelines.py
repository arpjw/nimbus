from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
import json
from database import get_session
from models.pipeline import Pipeline, PipelineRun
from api.routes.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


class PipelineCreate(BaseModel):
    workspace_id: str
    repo_id: str
    name: str
    description: Optional[str] = None
    config: dict
    schedule: Optional[str] = None


class PipelineRunRequest(BaseModel):
    repo_id: str
    workspace_id: str


@router.post("/")
async def create_pipeline(
    body: PipelineCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    pipeline = Pipeline(
        workspace_id=body.workspace_id,
        name=body.name,
        description=body.description,
        config=json.dumps(body.config),
        schedule=body.schedule,
    )
    session.add(pipeline)
    session.commit()
    session.refresh(pipeline)
    return pipeline


@router.get("/")
async def list_pipelines(
    workspace_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    pipelines = session.exec(
        select(Pipeline).where(Pipeline.workspace_id == workspace_id)
    ).all()
    return pipelines


@router.get("/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    pipeline = session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.post("/{pipeline_id}/run")
async def run_pipeline(
    pipeline_id: str,
    body: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    pipeline = session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    from services.pipeline_executor import execute_pipeline
    background_tasks.add_task(
        execute_pipeline,
        pipeline_id=pipeline_id,
        repo_id=body.repo_id,
        workspace_id=body.workspace_id,
        api_key_id=current_user.id,
    )
    return {"status": "started", "pipeline_id": pipeline_id}


@router.get("/{pipeline_id}/runs")
async def get_pipeline_runs(
    pipeline_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    runs = session.exec(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == pipeline_id)
        .order_by(PipelineRun.started_at.desc())
        .limit(20)
    ).all()
    return runs


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    pipeline = session.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    session.delete(pipeline)
    session.commit()
    return {"status": "deleted"}
