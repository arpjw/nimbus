import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models.automation import Automation
from services.auth import ApiKey, require_api_key
from services.automation_engine import AutomationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automations", tags=["automations"])
_engine = AutomationEngine()


class AutomationCreate(BaseModel):
    name: str
    repo_id: str
    task_template: str
    trigger_type: str
    trigger_config: dict
    enabled: bool = True


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    task_template: Optional[str] = None
    trigger_config: Optional[dict] = None
    enabled: Optional[bool] = None


class AutomationResponse(BaseModel):
    id: str
    name: str
    owner_key_id: str
    repo_id: str
    task_template: str
    trigger_type: str
    trigger_config: dict
    enabled: bool
    created_at: datetime
    last_triggered_at: Optional[datetime]
    last_task_id: Optional[str]


def _to_response(a: Automation) -> AutomationResponse:
    try:
        config = json.loads(a.trigger_config)
    except (json.JSONDecodeError, TypeError):
        config = {}
    return AutomationResponse(
        id=a.id,
        name=a.name,
        owner_key_id=a.owner_key_id,
        repo_id=a.repo_id,
        task_template=a.task_template,
        trigger_type=a.trigger_type,
        trigger_config=config,
        enabled=a.enabled,
        created_at=a.created_at,
        last_triggered_at=a.last_triggered_at,
        last_task_id=a.last_task_id,
    )


@router.post("/", response_model=AutomationResponse)
def create_automation(
    body: AutomationCreate,
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_key),
):
    automation = Automation(
        name=body.name,
        owner_key_id=api_key.id,
        repo_id=body.repo_id,
        task_template=body.task_template,
        trigger_type=body.trigger_type,
        trigger_config=json.dumps(body.trigger_config),
        enabled=body.enabled,
    )
    session.add(automation)
    session.commit()
    session.refresh(automation)

    if body.trigger_type == "cron" and body.enabled:
        _engine.schedule_all()

    return _to_response(automation)


@router.get("/", response_model=list[AutomationResponse])
def list_automations(
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_key),
):
    automations = session.exec(
        select(Automation).where(Automation.owner_key_id == api_key.id)
    ).all()
    return [_to_response(a) for a in automations]


@router.patch("/{automation_id}", response_model=AutomationResponse)
def update_automation(
    automation_id: str,
    body: AutomationUpdate,
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_key),
):
    automation = session.get(Automation, automation_id)
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    if automation.owner_key_id != api_key.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if body.name is not None:
        automation.name = body.name
    if body.task_template is not None:
        automation.task_template = body.task_template
    if body.trigger_config is not None:
        automation.trigger_config = json.dumps(body.trigger_config)
    if body.enabled is not None:
        automation.enabled = body.enabled

    session.add(automation)
    session.commit()
    session.refresh(automation)

    if automation.trigger_type == "cron":
        _engine.schedule_all()

    return _to_response(automation)


@router.delete("/{automation_id}")
def delete_automation(
    automation_id: str,
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_key),
):
    automation = session.get(Automation, automation_id)
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    if automation.owner_key_id != api_key.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    session.delete(automation)
    session.commit()

    if automation.trigger_type == "cron":
        _engine.schedule_all()

    return {"status": "deleted"}


@router.post("/webhook")
async def automation_webhook(request: Request):
    body = await request.json()
    headers = dict(request.headers)

    matching = _engine.evaluate_webhook(body, headers)
    triggered_tasks: list[str] = []

    for automation in matching:
        task_id = await _engine.trigger_automation(automation, body)
        if task_id:
            triggered_tasks.append(task_id)
            logger.info("Triggered automation %s -> task %s", automation.id, task_id)

    return {"triggered": len(triggered_tasks), "task_ids": triggered_tasks}
