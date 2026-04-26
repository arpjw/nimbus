import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlmodel import Session, select

from agent.orchestrator import run_task, _approval_events, _approval_results, _rag_service
from agent.reviewer_external import review_pr as _review_pr
from agent.test_generator import generate_tests
from api.ws import manager, get_or_create_queue, pump_queue_to_ws
from config import settings
from database import get_session
from github_app.github import post_pr_comment
from models.task import Task, Repo, Phase
from models.schemas import TaskCreate, TaskResponse
from services.auth import ApiKey, require_api_key, check_rate_limit

from services.review_rules import ReviewRulesService

router = APIRouter(prefix="/tasks", tags=["tasks"])
review_router = APIRouter(tags=["review"])
test_router = APIRouter(tags=["tests"])
rules_router = APIRouter(prefix="/repos", tags=["rules"])

_review_rules_service = ReviewRulesService()


class ReviewRequest(BaseModel):
    pr_url: str
    post: bool = False


@review_router.post("/review")
async def review_endpoint(body: ReviewRequest):
    review = await _review_pr(body.pr_url, settings.github_token)
    match = re.search(r"\*\*Verdict\*\*:\s*(APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION)", review)
    verdict = match.group(1) if match else "NEEDS_DISCUSSION"
    if body.post:
        await post_pr_comment(body.pr_url, review)
    return {"pr_url": body.pr_url, "review": review, "verdict": verdict}


@router.post("/", response_model=TaskResponse)
async def create_task(
    body: TaskCreate,
    session: Session = Depends(get_session),
    api_key: ApiKey = Depends(require_api_key),
):
    repo = session.get(Repo, body.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    await check_rate_limit(api_key)

    task = Task(
        workspace_id=body.workspace_id,
        repo_id=body.repo_id,
        description=body.description,
        issue_number=body.issue_number,
        repo_full_name=body.repo_full_name,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    if api_key.id != "local":
        api_key.task_count_month += 1
        api_key.last_used_at = datetime.now(timezone.utc)
        session.add(api_key)
        session.commit()

    queue = get_or_create_queue(task.id)
    asyncio.create_task(run_task(task, repo, queue, issue_number=body.issue_number, repo_full_name=body.repo_full_name, skill_name=body.skill, api_key_id=api_key.id))
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


@router.post("/{task_id}/approve-diff")
async def approve_diff(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    diff_key = task_id + ":diff"
    event = _approval_events.get(diff_key)
    if event is None:
        raise HTTPException(status_code=409, detail="Task is not awaiting diff approval")
    _approval_results[diff_key] = True
    event.set()
    return {"status": "approved"}


@router.post("/{task_id}/reject-diff")
async def reject_diff(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    diff_key = task_id + ":diff"
    event = _approval_events.get(diff_key)
    if event is None:
        raise HTTPException(status_code=409, detail="Task is not awaiting diff approval")
    _approval_results[diff_key] = False
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


class GenerateTestsRequest(BaseModel):
    repo_id: str
    file_path: str


def _derive_test_file_path(file_path: str) -> str:
    p = Path(file_path)
    ext = p.suffix.lower()
    stem = p.stem
    parent = p.parent

    if ext == ".py":
        return str(Path("tests") / f"test_{stem}.py")

    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        return str(parent / f"{stem}.test{ext}")

    if ext == ".go":
        return str(parent / f"{stem}_test.go")

    if ext == ".rs":
        return str(parent / f"{stem}_test.rs")

    return str(parent / f"{stem}.test{ext}")


def _find_workspace_file(repo_id: str, file_path: str, session: Session) -> tuple[Path, str]:
    tasks = session.exec(
        select(Task)
        .where(Task.repo_id == repo_id)
        .order_by(Task.created_at.desc())
    ).all()

    for task in tasks:
        workspace = settings.workspace_path / task.id
        candidate = workspace / file_path
        if candidate.exists():
            return workspace, candidate.read_text()

    raise HTTPException(status_code=404, detail=f"File not found in any workspace for repo {repo_id}")


@rules_router.get("/{repo_id}/rules")
async def list_rules(repo_id: str, session: Session = Depends(get_session)):
    repo = session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    return await _review_rules_service.list_rules(repo_id)


@rules_router.delete("/{repo_id}/rules/{rule_id}")
async def disable_rule(repo_id: str, rule_id: str, session: Session = Depends(get_session)):
    repo = session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    found = await _review_rules_service.disable_rule(repo_id, rule_id)
    if not found:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "disabled"}


@test_router.post("/generate-tests")
async def generate_tests_endpoint(
    body: GenerateTestsRequest,
    session: Session = Depends(get_session),
):
    repo = session.get(Repo, body.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    _, content = _find_workspace_file(body.repo_id, body.file_path, session)

    test_content = await generate_tests(
        file_path=body.file_path,
        content=content,
        repo_id=body.repo_id,
        rag_service=_rag_service,
    )

    test_file_path = _derive_test_file_path(body.file_path)

    return {
        "file_path": body.file_path,
        "test_file_path": test_file_path,
        "content": test_content,
    }
