import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select

from agent.orchestrator import run_task, _approval_events, _approval_results
from api.ws import manager, get_or_create_queue, pump_queue_to_ws
from database import get_session
from models.task import Task, Repo, Phase
from models.schemas import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
async def create_task(body: TaskCreate, session: Session = Depends(get_session)):
    repo = session.get(Repo, body.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    task = Task(
        workspace_id=body.workspace_id,
        repo_id=body.repo_id,
        description=body.description,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    queue = get_or_create_queue(task.id)
    asyncio.create_task(run_task(task, repo, queue))
    asyncio.create_task(pump_queue_to_ws(task.id))

    return task


@router.get("/", response_model=list[TaskResponse])
def list_tasks(workspace_id: str | None = None, session: Session = Depends(get_session)):
    q = select(Task)
    if workspace_id:
        q = q.where(Task.workspace_id == workspace_id)
    return session.exec(q.order_by(Task.created_at.desc())).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/approve")
async def approve_task(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    event = _approval_events.get(task_id)
    if event is None:
        raise HTTPException(status_code=409, detail="Task is not awaiting approval")
    _approval_results[task_id] = True
    event.set()
    return {"status": "approved"}


@router.post("/{task_id}/reject")
async def reject_task(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    event = _approval_events.get(task_id)
    if event is None:
        raise HTTPException(status_code=409, detail="Task is not awaiting approval")
    _approval_results[task_id] = False
    event.set()
    return {"status": "rejected"}


@router.websocket("/{task_id}/ws")
async def task_ws(task_id: str, ws: WebSocket):
    await manager.connect(task_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, ws)
