import asyncio
import logging

from sqlmodel import Session, select

from agent.orchestrator import run_task
from database import engine
from linear_app.linear_app import LinearApp
from models.task import Task, Repo, Workspace, LinearTeamRepoMap

logger = logging.getLogger(__name__)

_linear = LinearApp()


def _find_or_create_workspace_and_repo(
    session: Session, repo_url: str
) -> tuple[Workspace, Repo] | tuple[None, None]:
    repo = session.exec(select(Repo).where(Repo.url == repo_url)).first()
    if repo:
        workspace = session.get(Workspace, repo.workspace_id)
        return workspace, repo
    return None, None


def _queue_task(task: Task, repo: Repo) -> None:
    asyncio.create_task(run_task(task, repo))


async def _dispatch_from_issue(issue_id: str, team_id: str) -> None:
    issue = await _linear.get_issue(issue_id)
    if not issue:
        logger.warning("Linear issue not found: %s", issue_id)
        return

    title: str = issue.get("title", "")
    description: str = issue.get("description") or ""
    task_description = f"{title}\n\n{description}".strip()

    with Session(engine) as session:
        mapping = session.exec(
            select(LinearTeamRepoMap).where(LinearTeamRepoMap.linear_team_id == team_id)
        ).first()

        if not mapping:
            logger.warning("No repo mapping for Linear team: %s", team_id)
            return

        workspace, repo = _find_or_create_workspace_and_repo(session, mapping.github_repo_url)

        if not workspace or not repo:
            logger.warning("Repo not indexed for URL: %s", mapping.github_repo_url)
            return

        task = Task(
            workspace_id=workspace.id,
            repo_id=repo.id,
            description=task_description,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id = task.id
        _queue_task(task, repo)

    await _linear.post_comment(
        issue_id,
        f"Nimbus is working on this. Task ID: {task_id}",
    )


async def handle_issue_assigned(payload: dict) -> None:
    issue = payload.get("data", {})
    assignees = issue.get("assignees", [])
    is_nimbus = any(
        a.get("name", "").lower() == "nimbus" or a.get("displayName", "").lower() == "nimbus"
        for a in assignees
    )
    if not is_nimbus:
        return

    issue_id: str = issue.get("id", "")
    team_id: str = issue.get("team", {}).get("id", "")
    if issue_id and team_id:
        await _dispatch_from_issue(issue_id, team_id)


async def handle_issue_labeled(payload: dict) -> None:
    label_name: str = payload.get("data", {}).get("label", {}).get("name", "").lower()
    if label_name != "nimbus":
        return

    issue = payload.get("data", {})
    issue_id: str = issue.get("id", "")
    team_id: str = issue.get("team", {}).get("id", "")
    if issue_id and team_id:
        await _dispatch_from_issue(issue_id, team_id)


async def handle_webhook(payload: dict) -> None:
    action: str = payload.get("action", "")
    event_type: str = payload.get("type", "")

    if event_type == "Issue":
        if action == "update" and "assignees" in payload.get("updatedFrom", {}):
            await handle_issue_assigned(payload)
        elif action == "update" and payload.get("data", {}).get("labelIds"):
            await handle_issue_labeled(payload)
