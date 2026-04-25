import httpx
from config import settings

_GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def post_reaction(repo_full_name: str, comment_id: int, reaction: str) -> None:
    url = f"{_GITHUB_API}/repos/{repo_full_name}/issues/comments/{comment_id}/reactions"
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=_headers(), json={"content": reaction})


async def post_comment(repo_full_name: str, issue_number: int, body: str) -> None:
    url = f"{_GITHUB_API}/repos/{repo_full_name}/issues/{issue_number}/comments"
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=_headers(), json={"body": body})
