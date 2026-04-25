"""
Orchestrator: drives the full Nimbus workflow across all phases, emitting
real-time events to a WebSocket queue consumed by the frontend.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, AsyncGenerator

from sqlmodel import Session

from agent.planner import generate_plan, Plan
from agent.implementer import execute_plan
from services.memory import write_repo_memory, read_repo_memory
from agent.verifier import verify
from agent.reviewer import self_review, respond_to_comments
from config import settings
from database import engine
from github_app.github import post_comment
from models.task import Task, Phase, Repo, RepoStatus
from services.embedding import EmbeddingService
from services.rag import RAGService
from services.vector_store import VectorStore
from tools.git_tools import GitManager
from tools.file_tools import list_files, read_file
from services.chunker import chunk_file

_embedding_service = EmbeddingService()
_vector_store = VectorStore()
_rag_service = RAGService(_embedding_service, _vector_store)
_git_manager = GitManager()

_approval_events: dict[str, asyncio.Event] = {}
_approval_results: dict[str, bool] = {}

Emitter = Callable[[Phase, str, dict | None], None]


async def _emit_event(queue: asyncio.Queue, task_id: str, phase: Phase, message: str, data: dict | None = None):
    await queue.put({"task_id": task_id, "phase": phase.value, "message": message, "ts": datetime.utcnow().isoformat(), "data": data or {}})


def _update_task(task_id: str, **kwargs):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return
        for k, v in kwargs.items():
            setattr(task, k, v)
        task.updated_at = datetime.utcnow()
        session.add(task)
        session.commit()


async def _index_repository(repo: Repo, workspace: Path) -> None:
    files = await list_files(workspace)
    all_docs, all_ids, all_metas = [], [], []
    bm25_docs, bm25_metas = [], []

    for file_info in files:
        try:
            content = await read_file(workspace, file_info["path"])
        except Exception:
            continue

        file_chunks = await chunk_file(file_info["path"], content, repo.id)
        for chunk in file_chunks:
            meta = {
                "chunk_id": chunk["chunk_id"],
                "repo_id": chunk["repo_id"],
                "file_path": chunk["file_path"],
                "language": chunk["language"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "symbol_name": chunk["symbol_name"] or "",
                "symbol_type": chunk["symbol_type"],
            }
            all_docs.append(chunk["text"])
            all_ids.append(chunk["chunk_id"])
            all_metas.append(meta)
            bm25_docs.append(chunk["text"])
            bm25_metas.append(meta)

    if all_docs:
        embeddings = await _embedding_service.embed_documents(all_docs)
        _vector_store.upsert(repo.id, all_ids, embeddings, all_docs, all_metas)
        _rag_service.prime_bm25(repo.id, bm25_docs, bm25_metas)

    with Session(engine) as session:
        db_repo = session.get(Repo, repo.id)
        if db_repo:
            db_repo.status = RepoStatus.INDEXED
            db_repo.indexed_at = datetime.utcnow()
            db_repo.file_count = len(files)
            db_repo.chunk_count = len(all_docs)
            session.add(db_repo)
            session.commit()


async def _build_file_tree(workspace: Path) -> str:
    files = await list_files(workspace, max_files=500)
    return "\n".join(f["path"] for f in files)


async def run_task(
    task: Task,
    repo: Repo,
    queue: asyncio.Queue,
    issue_number: int | None = None,
    repo_full_name: str | None = None,
) -> None:
    emit = lambda phase, msg, data=None: _emit_event(queue, task.id, phase, msg, data)

    workspace = settings.workspace_path / task.id
    workspace.mkdir(parents=True, exist_ok=True)

    plan: Plan | None = None
    verification = None

    try:
        await emit(Phase.CLONING, f"Cloning {repo.url}...")
        _update_task(task.id, phase=Phase.CLONING)
        git_repo = await _git_manager.clone(repo.url, workspace)

        branch_name = _git_manager.generate_branch_name(task.description)
        await _git_manager.create_branch(git_repo, branch_name)
        _update_task(task.id, branch_name=branch_name)
        await emit(Phase.CLONING, f"Branch created: {branch_name}")

        await emit(Phase.INDEXING, "Building Voyage AI code embeddings (voyage-code-2)...")
        _update_task(task.id, phase=Phase.INDEXING)
        await _index_repository(repo, workspace)
        await emit(Phase.INDEXING, f"Indexed {repo.chunk_count} chunks across {repo.file_count} files")

        await emit(Phase.PLANNING, "Generating implementation plan (Claude Opus)...")
        _update_task(task.id, phase=Phase.PLANNING)
        file_tree = await _build_file_tree(workspace)
        memories = await read_repo_memory(repo.id, task.description)
        plan = await generate_plan(task.description, [repo.id], _rag_service, file_tree, memories=memories)
        _update_task(task.id, plan=plan.raw)
        await emit(Phase.PLANNING, f"Plan: {plan.summary}", {"changes": len(plan.changes)})

        for change in plan.changes:
            await emit(Phase.PLANNING, f"  [{change.action.upper()}] {change.path}: {change.description[:80]}")

        _approval_events[task.id] = asyncio.Event()
        _update_task(task.id, phase=Phase.AWAITING_APPROVAL)
        await emit(
            Phase.AWAITING_APPROVAL,
            f"Plan ready: {len(plan.changes)} change(s) require approval",
            {"changes": [{"path": c.path, "action": c.action, "description": c.description} for c in plan.changes]},
        )
        try:
            await asyncio.wait_for(_approval_events[task.id].wait(), timeout=300)
            approved = _approval_results.pop(task.id, True)
        except asyncio.TimeoutError:
            _approval_results.pop(task.id, None)
            _update_task(task.id, phase=Phase.FAILED, error="Approval timeout")
            await emit(Phase.FAILED, "Approval timeout")
            return
        finally:
            _approval_events.pop(task.id, None)

        if not approved:
            _update_task(task.id, phase=Phase.FAILED, error="Rejected by user")
            await emit(Phase.FAILED, "Rejected by user")
            return

        for iteration in range(settings.max_implement_iterations):
            _update_task(task.id, phase=Phase.IMPLEMENTING, iteration=iteration + 1)
            await emit(Phase.IMPLEMENTING, f"Implementing (iteration {iteration + 1}/{settings.max_implement_iterations})...")

            async for log_line in execute_plan(plan, workspace):
                await emit(Phase.IMPLEMENTING, log_line)

            await _git_manager.commit_all(git_repo, f"nimbus: implement task (iteration {iteration + 1})")

            _update_task(task.id, phase=Phase.VERIFYING)
            await emit(Phase.VERIFYING, "Running verification checks...")
            verification = await verify(workspace)

            await emit(Phase.VERIFYING, f"Checks: {', '.join(verification.checks_run)} | Passed: {verification.passed}")

            if verification.passed:
                break

            if iteration < settings.max_implement_iterations - 1:
                _update_task(task.id, phase=Phase.FIXING)
                await emit(Phase.FIXING, f"Errors found — regenerating plan...")
                error_context = "\n".join(verification.errors)
                plan = await generate_plan(
                    f"Original task: {task.description}\n\nFix these errors:\n{error_context}",
                    [repo.id], _rag_service, file_tree
                )
            else:
                await emit(Phase.FIXING, "Max iterations reached — proceeding with current state")

        _update_task(task.id, phase=Phase.REVIEWING)
        await emit(Phase.REVIEWING, "Pushing branch and creating PR...")
        await _git_manager.push(git_repo, branch_name)

        diff_raw = git_repo.git.diff("origin/HEAD...HEAD")
        lines_changed = sum(
            1 for line in diff_raw.splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        )
        diff_string = diff_raw if len(diff_raw) <= 8000 else diff_raw[:8000] + "\n... (truncated)"

        diff_key = task.id + ":diff"
        _approval_events[diff_key] = asyncio.Event()
        _update_task(task.id, phase=Phase.AWAITING_DIFF_APPROVAL)
        await emit(
            Phase.AWAITING_DIFF_APPROVAL,
            f"Diff ready for review -- {lines_changed} lines changed",
            {"diff": diff_string, "lines_changed": lines_changed},
        )
        try:
            await asyncio.wait_for(_approval_events[diff_key].wait(), timeout=300)
            diff_approved = _approval_results.pop(diff_key, True)
        except asyncio.TimeoutError:
            _approval_results.pop(diff_key, None)
            _update_task(task.id, phase=Phase.FAILED, error="Diff approval timeout")
            await emit(Phase.FAILED, "Diff approval timeout")
            return
        finally:
            _approval_events.pop(diff_key, None)

        if not diff_approved:
            _update_task(task.id, phase=Phase.FAILED, error="Diff rejected by user")
            await emit(Phase.FAILED, "Diff rejected by user")
            return

        review_body = "Automated implementation by **Nimbus** -- awaiting self-review..."
        pr_url = await _git_manager.create_pr(repo.url, branch_name, task.description, review_body)
        _update_task(task.id, pr_url=pr_url)
        await emit(Phase.REVIEWING, f"PR created: {pr_url}", {"pr_url": pr_url})

        await emit(Phase.REVIEWING, "Performing self-review (Claude Sonnet)...")
        review_result = await self_review(pr_url, _git_manager)
        await _git_manager.post_pr_comment(pr_url, review_result.body)
        await emit(Phase.REVIEWING, f"Self-review posted — verdict: {review_result.verdict} ({review_result.issues_found} issues)")

        _update_task(task.id, phase=Phase.CLEANUP)
        await emit(Phase.CLEANUP, "Cleaning up workspace...")
        await _git_manager.cleanup(workspace)

        _update_task(task.id, phase=Phase.DONE, completed_at=datetime.utcnow())
        await emit(Phase.DONE, "Task complete!", {"pr_url": pr_url, "verdict": review_result.verdict})

        if issue_number is not None and repo_full_name is not None:
            try:
                await post_comment(
                    repo_full_name,
                    issue_number,
                    f"**Nimbus** opened a PR: {pr_url}\n\nSelf-review verdict: {review_result.verdict}",
                )
            except Exception:
                pass

        asyncio.create_task(respond_to_comments(pr_url, _git_manager))

        try:
            await write_repo_memory(repo.id, task.description, plan.raw, verification.passed, None)
        except Exception:
            pass

    except Exception as exc:
        error_str = str(exc)[:500]
        _update_task(task.id, phase=Phase.FAILED, error=error_str)
        await emit(Phase.FAILED, f"Task failed: {exc}")
        if issue_number is not None and repo_full_name is not None:
            try:
                await post_comment(repo_full_name, issue_number, f"**Nimbus** failed: {error_str}")
            except Exception:
                pass
        if plan is not None:
            try:
                verification_passed = verification.passed if verification is not None else False
                await write_repo_memory(repo.id, task.description, plan.raw, verification_passed, error_str)
            except Exception:
                pass
        try:
            await _git_manager.cleanup(workspace)
        except Exception:
            pass
