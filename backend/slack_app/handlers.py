import asyncio
import re

from sqlmodel import Session, select

from agent.reviewer_external import review_pr
from api.ws import get_or_create_queue, pump_queue_to_ws
from config import settings
from database import engine
from github_app.handlers import _find_or_create_workspace_and_repo
from models.task import ChannelRepoMap, Repo, Task, Workspace
from slack_app.slack_app import SlackApp


def _get_channel_mapping(session: Session, channel_id: str) -> ChannelRepoMap | None:
    return session.exec(select(ChannelRepoMap).where(ChannelRepoMap.channel_id == channel_id)).first()


def _upsert_channel_mapping(session: Session, channel_id: str, repo_url: str, workspace_id: str) -> None:
    existing = _get_channel_mapping(session, channel_id)
    if existing:
        existing.repo_url = repo_url
        existing.workspace_id = workspace_id
        session.add(existing)
    else:
        session.add(ChannelRepoMap(channel_id=channel_id, repo_url=repo_url, workspace_id=workspace_id))
    session.commit()


async def _handle_run(channel_id: str, args: str) -> dict:
    repo_match = re.search(r"--repo\s+(\S+)", args)
    repo_full = repo_match.group(1) if repo_match else None
    task_desc = re.sub(r"--repo\s+\S+", "", args).strip()

    if not task_desc:
        return {"response_type": "ephemeral", "text": "Usage: /nimbus run <task> [--repo owner/repo]"}

    with Session(engine) as session:
        if repo_full:
            repo_url = f"https://github.com/{repo_full}"
            workspace, repo = _find_or_create_workspace_and_repo(session, repo_url, repo_full)
            _upsert_channel_mapping(session, channel_id, repo_url, workspace.id)
            session.refresh(workspace)
            session.refresh(repo)
        else:
            mapping = _get_channel_mapping(session, channel_id)
            if not mapping:
                return {
                    "response_type": "ephemeral",
                    "text": "No repo mapped to this channel. Use: /nimbus run <task> --repo owner/repo",
                }
            repo_url = mapping.repo_url
            repo = session.exec(select(Repo).where(Repo.url == repo_url)).first()
            if not repo:
                return {"response_type": "ephemeral", "text": f"Repo not found: {repo_url}"}
            workspace = session.get(Workspace, repo.workspace_id)

        task = Task(workspace_id=workspace.id, repo_id=repo.id, description=task_desc)
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id = task.id

    from agent.orchestrator import run_task

    queue = get_or_create_queue(task_id)
    asyncio.create_task(run_task(task, repo, queue, slack_channel=channel_id))
    asyncio.create_task(pump_queue_to_ws(task_id))

    return {"response_type": "in_channel", "text": f":hourglass: On it... Task `{task_id[:8]}` queued."}


async def _handle_review(channel_id: str, args: str) -> dict:
    pr_url = args.strip()
    if not pr_url or not pr_url.startswith("https://github.com/"):
        return {"response_type": "ephemeral", "text": "Usage: /nimbus review <github_pr_url>"}

    async def _do_review() -> None:
        app = SlackApp()
        try:
            review = await review_pr(pr_url, settings.github_token)
            await app.post_message(channel_id, f"*Code Review for {pr_url}*\n\n{review[:2900]}")
        except Exception as exc:
            await app.post_message(channel_id, f":x: Review failed: {exc}")

    asyncio.create_task(_do_review())
    return {"response_type": "ephemeral", "text": f":mag: Running review for {pr_url}..."}


async def _handle_status(channel_id: str) -> dict:
    with Session(engine) as session:
        mapping = _get_channel_mapping(session, channel_id)
        if not mapping:
            return {"response_type": "ephemeral", "text": "No repo mapped to this channel."}

        repo = session.exec(select(Repo).where(Repo.url == mapping.repo_url)).first()
        if not repo:
            return {"response_type": "ephemeral", "text": f"Repo not found: {mapping.repo_url}"}

        tasks = session.exec(
            select(Task).where(Task.repo_id == repo.id).order_by(Task.created_at.desc()).limit(3)
        ).all()

    if not tasks:
        return {"response_type": "ephemeral", "text": f"No tasks found for {mapping.repo_url}"}

    lines = [f"*Last {len(tasks)} task(s) for `{mapping.repo_url}`*"]
    for t in tasks:
        pr_part = f" -> {t.pr_url}" if t.pr_url else ""
        lines.append(f"- [{t.phase.value}] `{t.description[:60]}`{pr_part}")

    return {"response_type": "ephemeral", "text": "\n".join(lines)}


async def handle_slash_command(payload: dict) -> dict:
    command_text = payload.get("text", "").strip()
    channel_id = payload.get("channel_id", "")

    if not command_text:
        return {
            "response_type": "ephemeral",
            "text": "Usage: /nimbus run <task> [--repo owner/repo] | /nimbus review <pr_url> | /nimbus status",
        }

    parts = command_text.split(maxsplit=1)
    subcommand = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if subcommand == "run":
        return await _handle_run(channel_id, args)
    if subcommand == "review":
        return await _handle_review(channel_id, args)
    if subcommand == "status":
        return await _handle_status(channel_id)

    return {
        "response_type": "ephemeral",
        "text": "Unknown command. Usage: /nimbus run <task> [--repo owner/repo] | /nimbus review <pr_url> | /nimbus status",
    }


async def handle_events(payload: dict) -> None:
    pass
