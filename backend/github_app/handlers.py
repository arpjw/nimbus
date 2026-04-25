import asyncio
import logging
from sqlmodel import Session, select

from agent.orchestrator import run_task
from api.ws import get_or_create_queue, pump_queue_to_ws
from database import engine
from models.task import Task, Repo, Workspace
from github_app.github import post_reaction

logger = logging.getLogger(__name__)


def _find_or_create_workspace_and_repo(session: Session, repo_url: str, repo_full_name: str) -> tuple[Workspace, Repo]:
    repo_name = repo_full_name.split("/")[-1]

    repo = session.exec(select(Repo).where(Repo.url == repo_url)).first()
    if repo:
        workspace = session.get(Workspace, repo.workspace_id)
        return workspace, repo

    workspace = session.exec(select(Workspace).where(Workspace.name == repo_full_name)).first()
    if not workspace:
        workspace = Workspace(name=repo_full_name, description=f"GitHub repo {repo_full_name}")
        session.add(workspace)
        session.flush()

    repo = Repo(workspace_id=workspace.id, url=repo_url, name=repo_name)
    session.add(repo)
    session.commit()
    session.refresh(workspace)
    session.refresh(repo)
    return workspace, repo


def _queue_task(task: Task, repo: Repo) -> None:
    queue = get_or_create_queue(task.id)
    asyncio.create_task(run_task(task, repo, queue))
    asyncio.create_task(pump_queue_to_ws(task.id))


async def handle_issue_comment(payload: dict) -> None:
    if payload.get("action") != "created":
        return

    comment_body: str = payload.get("comment", {}).get("body", "")
    if not comment_body.startswith("/nimbus "):
        return

    first_line = comment_body.splitlines()[0]
    command = first_line[len("/nimbus "):]

    repo_url: str = payload["repository"]["html_url"]
    repo_full_name: str = payload["repository"]["full_name"]
    comment_id: int = payload["comment"]["id"]

    with Session(engine) as session:
        workspace, repo = _find_or_create_workspace_and_repo(session, repo_url, repo_full_name)

        task = Task(
            workspace_id=workspace.id,
            repo_id=repo.id,
            description=command,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        _queue_task(task, repo)

    await post_reaction(repo_full_name, comment_id, "+1")


async def handle_issues(payload: dict) -> None:
    if payload.get("action") != "labeled":
        return

    label_name: str = payload.get("label", {}).get("name", "")
    if label_name != "nimbus":
        return

    issue = payload["issue"]
    title: str = issue.get("title", "")
    body: str = issue.get("body") or ""
    description = f"{title}\n\n{body}".strip()

    repo_url: str = payload["repository"]["html_url"]
    repo_full_name: str = payload["repository"]["full_name"]

    with Session(engine) as session:
        workspace, repo = _find_or_create_workspace_and_repo(session, repo_url, repo_full_name)

        task = Task(
            workspace_id=workspace.id,
            repo_id=repo.id,
            description=description,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        _queue_task(task, repo)


async def handle_pull_request(payload: dict) -> None:
    return
