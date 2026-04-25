import httpx
import anthropic

from config import settings

_GITHUB_API = "https://api.github.com"
_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = (
    "You are a senior engineer performing a thorough code review.\n"
    "Review this PR diff and produce structured feedback covering:\n"
    "correctness, edge cases, performance implications, security concerns,\n"
    "and style/maintainability. Format your response as:\n\n"
    "## Code Review\n\n"
    "**Summary**: one paragraph overview\n\n"
    "**Issues**\n"
    "- [CRITICAL|MINOR|NIT] `file:line` -- description\n\n"
    "**Suggestions**\n"
    "- description\n\n"
    "**Verdict**: APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION"
)


def _parse_pr_url(pr_url: str) -> tuple[str, int]:
    parts = pr_url.rstrip("/").split("/")
    repo_full = f"{parts[-4]}/{parts[-3]}"
    number = int(parts[-1])
    return repo_full, number


async def review_pr(pr_url: str, github_token: str) -> str:
    repo_full, number = _parse_pr_url(pr_url)

    json_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    diff_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=30.0) as http:
        meta_resp = await http.get(
            f"{_GITHUB_API}/repos/{repo_full}/pulls/{number}",
            headers=json_headers,
        )
        meta_resp.raise_for_status()
        meta = meta_resp.json()

        diff_resp = await http.get(
            f"{_GITHUB_API}/repos/{repo_full}/pulls/{number}",
            headers=diff_headers,
        )
        diff_resp.raise_for_status()
        diff = diff_resp.text

    title = meta.get("title", "")
    body = meta.get("body", "") or ""
    author = meta.get("user", {}).get("login", "")

    user_content = f"PR: {title}\nAuthor: {author}\nDescription: {body}\n\nDiff:\n{diff}"

    response = await _client.messages.create(
        model=settings.reviewer_model,
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    return response.content[0].text
