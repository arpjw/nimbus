import asyncio
import logging
import httpx
from sqlmodel import Session, select

from agent.orchestrator import run_task
from api.ws import get_or_create_queue, pump_queue_to_ws
from config import settings
from database import engine
from models.task import Task, Repo, Workspace
from github_app.github import post_reaction, post_comment
from services.review_rules import ReviewRulesService

_rules_service = ReviewRulesService()
_GITHUB_API = "https://api.github.com"
_NIMBUS_BOT_USER = "nimbus[bot]"

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


def _queue_task(
    task: Task,
    repo: Repo,
    issue_number: int | None = None,
    repo_full_name: str | None = None,
) -> None:
    queue = get_or_create_queue(task.id)
    asyncio.create_task(run_task(task, repo, queue, issue_number=issue_number, repo_full_name=repo_full_name))
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
    issue_number: int = issue["number"]
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
            issue_number=issue_number,
            repo_full_name=repo_full_name,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        _queue_task(task, repo, issue_number=issue_number, repo_full_name=repo_full_name)

    await post_comment(
        repo_full_name,
        issue_number,
        "**Nimbus** is on it. Task queued -- I'll update this issue when the PR is ready.",
    )


async def handle_pull_request(payload: dict) -> None:
    return


def _repo_id_from_url(repo_url: str, session: Session) -> str | None:
    repo = session.exec(select(Repo).where(Repo.url == repo_url)).first()
    return repo.id if repo else None


async def _fetch_pr_diff(repo_full_name: str, pr_number: int) -> str:
    headers = {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"{_GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}",
            headers=headers,
        )
        if resp.is_success:
            return resp.text
    return ""


async def handle_pull_request_review(payload: dict) -> None:
    if payload.get("action") != "submitted":
        return

    review = payload.get("review", {})
    reviewer_login: str = review.get("user", {}).get("login", "")
    if reviewer_login == _NIMBUS_BOT_USER:
        return

    body: str = review.get("body") or ""
    pr = payload.get("pull_request", {})
    pr_number: int = pr.get("number", 0)
    repo_url: str = payload["repository"]["html_url"]
    repo_full_name: str = payload["repository"]["full_name"]

    review_comments_url = review.get("_links", {}).get("html", {}).get("href", "")

    with Session(engine) as session:
        repo_id = _repo_id_from_url(repo_url, session)

    if not repo_id:
        return

    diff = await _fetch_pr_diff(repo_full_name, pr_number)

    comments = [c.strip() for c in [body] if c.strip()]

    rules = await _rules_service.extract_candidates(repo_id, diff, comments)
    for rule in rules:
        await _rules_service.add_candidate(repo_id, rule)


async def handle_issue_comment_reaction(payload: dict) -> None:
    if payload.get("action") != "created":
        return

    reaction = payload.get("reaction", {})
    content: str = reaction.get("content", "")
    if content not in ("+1", "-1"):
        return

    comment = payload.get("comment", {})
    comment_user: str = comment.get("user", {}).get("login", "")
    if comment_user != _NIMBUS_BOT_USER:
        return

    github_comment_id: int = comment.get("id", 0)
    if not github_comment_id:
        return

    repo_url: str = payload.get("repository", {}).get("html_url", "")
    if not repo_url:
        return

    with Session(engine) as session:
        repo_id = _repo_id_from_url(repo_url, session)

    if not repo_id:
        return

    rule_ids = _rules_service.get_comment_rules(repo_id, github_comment_id)
    positive = content == "+1"
    for rule_id in rule_ids:
        await _rules_service.record_signal(repo_id, rule_id, positive=positive)
