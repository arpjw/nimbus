import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import git
from github import Auth, Github

from config import settings


class GitManager:
    def __init__(self):
        self._gh = Github(auth=Auth.Token(settings.github_token))

    async def clone(self, repo_url: str, dest: Path) -> git.Repo:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(
            None,
            lambda: git.Repo.clone_from(
                self._inject_token(repo_url), str(dest), depth=1
            ),
        )
        return repo

    def _inject_token(self, url: str) -> str:
        if url.startswith("https://github.com/"):
            return url.replace(
                "https://github.com/",
                f"https://{settings.github_token}@github.com/",
            )
        return url

    async def create_branch(self, repo: git.Repo, branch_name: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: repo.git.checkout("-b", branch_name))

    async def commit_all(self, repo: git.Repo, message: str) -> Optional[str]:
        loop = asyncio.get_event_loop()
        def _commit():
            repo.git.add(".")
            if not repo.index.diff("HEAD") and not repo.untracked_files:
                return None
            repo.index.commit(message)
            return repo.head.commit.hexsha
        return await loop.run_in_executor(None, _commit)

    async def push(self, repo: git.Repo, branch_name: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: repo.git.push("origin", branch_name, "--set-upstream")
        )

    async def create_pr(
        self,
        repo_url: str,
        branch_name: str,
        task_description: str,
        body: str,
    ) -> str:
        loop = asyncio.get_event_loop()
        repo_path = repo_url.rstrip("/").replace("https://github.com/", "")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]

        def _create():
            gh_repo = self._gh.get_repo(repo_path)
            default = gh_repo.default_branch
            title = f"[Nimbus] {task_description[:72]}"
            pr = gh_repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=default,
            )
            return pr.html_url

        return await loop.run_in_executor(None, _create)

    async def get_pr_diff(self, pr_url: str) -> str:
        import httpx
        parts = pr_url.rstrip("/").split("/")
        pr_number = int(parts[-1])
        repo_path = "/".join(parts[-4:-2])
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}",
                headers={
                    "Authorization": f"Bearer {settings.github_token}",
                    "Accept": "application/vnd.github.v3.diff",
                },
            )
            resp.raise_for_status()
            return resp.text

    async def post_pr_comment(self, pr_url: str, body: str) -> None:
        parts = pr_url.rstrip("/").split("/")
        pr_number = int(parts[-1])
        repo_path = "/".join(parts[-4:-2])
        loop = asyncio.get_event_loop()
        def _post():
            gh_repo = self._gh.get_repo(repo_path)
            pr = gh_repo.get_pull(pr_number)
            pr.create_issue_comment(body)
        await loop.run_in_executor(None, _post)

    async def get_pr_comments(self, pr_url: str) -> list[dict]:
        parts = pr_url.rstrip("/").split("/")
        pr_number = int(parts[-1])
        repo_path = "/".join(parts[-4:-2])
        loop = asyncio.get_event_loop()
        def _get():
            gh_repo = self._gh.get_repo(repo_path)
            pr = gh_repo.get_pull(pr_number)
            return [
                {"author": c.user.login, "body": c.body, "created_at": c.created_at.isoformat()}
                for c in pr.get_issue_comments()
            ]
        return await loop.run_in_executor(None, _get)

    async def cleanup(self, path: Path) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, shutil.rmtree, str(path), True)

    def generate_branch_name(self, task_description: str) -> str:
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", task_description.lower())[:40].strip("-")
        ts = datetime.utcnow().strftime("%Y%m%d%H%M")
        return f"nimbus/{slug}-{ts}"
