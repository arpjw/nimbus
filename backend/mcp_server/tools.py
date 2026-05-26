from __future__ import annotations

import asyncio
from typing import Optional

from sqlmodel import Session, select

from database import engine
from models.task import Task, Repo, Workspace, Phase


async def create_task(
    repo: str,
    description: str,
    auto_approve: bool = False,
    api_key_id: Optional[str] = None,
) -> dict:
    with Session(engine) as session:
        repo_obj = session.exec(
            select(Repo).where(
                (Repo.url.contains(repo)) | (Repo.name == repo)
            )
        ).first()
        if not repo_obj:
            return {"error": f"Repo not found: {repo}. Index it first via `nimbus reindex`."}

        task = Task(
            workspace_id=repo_obj.workspace_id,
            repo_id=repo_obj.id,
            description=description,
            api_key_id=api_key_id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id = task.id

    from agent.orchestrator import run_task
    if auto_approve:
        asyncio.create_task(_run_with_auto_approve(task_id, task, repo_obj))
    else:
        asyncio.create_task(run_task(task, repo_obj, api_key_id=api_key_id))

    return {"task_id": task_id, "phase": Phase.QUEUED.value}


async def _run_with_auto_approve(task_id: str, task: Task, repo: Repo) -> None:
    from agent.orchestrator import run_task
    from redis_client import get_redis
    import json

    redis_client = await get_redis()
    result_key = f"nimbus:approval-result:{task_id}"

    async def _approve_when_ready() -> None:
        await asyncio.sleep(2)
        await redis_client.rpush(result_key, json.dumps({"approved": True}))

    asyncio.create_task(_approve_when_ready())
    await run_task(task, repo, api_key_id=task.api_key_id)


async def get_task_status(task_id: str) -> dict:
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return {"error": f"Task not found: {task_id}"}
        return {
            "task_id": task.id,
            "phase": task.phase.value,
            "pr_url": task.pr_url,
            "error": task.error,
            "confidence_score": task.confidence_score,
            "estimated_cost_usd": task.estimated_cost_usd,
        }


async def search_codebase(repo: str, query: str, top_k: int = 10) -> list[dict]:
    with Session(engine) as session:
        repo_obj = session.exec(
            select(Repo).where(
                (Repo.url.contains(repo)) | (Repo.name == repo)
            )
        ).first()
        if not repo_obj:
            return [{"error": f"Repo not found: {repo}"}]

    from nimbus_core.embedding import EmbeddingService
    from nimbus_core.rag import RAGService
    from nimbus_core.vector_store import VectorStore

    rag = RAGService(EmbeddingService(), VectorStore())
    chunks = await rag.query(query, repo_ids=[repo_obj.id], top_k=top_k)
    return [{"path": c.path, "content": c.content[:500], "score": c.score} for c in chunks]


async def review_diff(diff: str, repo_id: Optional[str] = None) -> dict:
    from config import settings
    from services.llm_client import instrumented_anthropic_client
    from agent.reviewer import SELF_REVIEW_SYSTEM

    client = instrumented_anthropic_client(role="reviewer", task_id=None, api_key_id=None)
    try:
        resp = await client.messages.create(
            model=settings.reviewer_model,
            max_tokens=2048,
            system=SELF_REVIEW_SYSTEM,
            messages=[{"role": "user", "content": f"Review this diff:\n\n{diff[:8000]}"}],
        )
        body = resp.content[0].text.strip()
        verdict = "APPROVE"
        if "REQUEST_CHANGES" in body or "request_changes" in body.lower():
            verdict = "REQUEST_CHANGES"
        elif "COMMENT" in body:
            verdict = "COMMENT"
        return {"verdict": verdict, "body": body}
    except Exception as exc:
        return {"error": str(exc), "verdict": "SKIPPED", "body": ""}
