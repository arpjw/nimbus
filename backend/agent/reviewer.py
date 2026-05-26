from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from config import settings
from tools.git_tools import GitManager
from services.llm_client import instrumented_anthropic_client

client = instrumented_anthropic_client("reviewer")


def _openai_client_or_none() -> Any:
    if not settings.openai_api_key:
        return None
    try:
        import openai
        return openai.AsyncOpenAI(api_key=settings.openai_api_key)
    except ImportError:
        return None


async def _review_with_openai(oai_client: Any, diff: str) -> str:
    response = await oai_client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SELF_REVIEW_SYSTEM},
            {"role": "user", "content": f"## PR Diff\n```diff\n{diff}\n```\n\nReview this."},
        ],
    )
    return response.choices[0].message.content.strip()


@dataclass
class ReviewResult:
    body: str
    issues_found: int
    verdict: str


SELF_REVIEW_SYSTEM = """You are a senior engineer performing a self-code-review on a PR
you just created. Be critical and honest. Your goal is to catch bugs, missed edge cases,
style inconsistencies, and incomplete implementations before a human reviews.

Format your review as:

## Self-Review

**Verdict**: APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION

**Summary**: One paragraph overview of what changed and why.

**Issues Found** (if any):
- [CRITICAL/MINOR] File:line -- description

**What I verified**:
- ...

Keep it concise. Flag real issues only, not style nitpicks.
"""

COMMENT_RESPONSE_SYSTEM = """You are the engineer who wrote this PR. A human reviewer
has left comments. Respond professionally and technically to each comment.
For each actionable comment, indicate whether you'll fix it (and how) or why it's correct as-is.
"""


_FILE_SPLIT_MARKER = "\ndiff --git "
_MAX_SINGLE_DIFF = 150_000


async def _review_large_diff(diff: str) -> str:
    file_diffs = diff.split(_FILE_SPLIT_MARKER)
    per_file_bodies: list[str] = []
    for part in file_diffs:
        if not part.strip():
            continue
        chunk = ("diff --git " + part) if not part.startswith("diff --git ") else part
        resp = await client.messages.create(
            model=settings.reviewer_model,
            max_tokens=1024,
            system=SELF_REVIEW_SYSTEM,
            messages=[{"role": "user", "content": f"## File diff\n```diff\n{chunk}\n```\n\nReview this file only."}],
        )
        per_file_bodies.append(resp.content[0].text.strip())

    combined_prompt = "Synthesize a single review verdict from these per-file reviews:\n\n" + "\n\n---\n\n".join(per_file_bodies)
    synthesis = await client.messages.create(
        model=settings.reviewer_model,
        max_tokens=2048,
        system=SELF_REVIEW_SYSTEM,
        messages=[{"role": "user", "content": combined_prompt}],
    )
    return synthesis.content[0].text.strip()


async def self_review(
    pr_url: str,
    git_manager: GitManager,
    structured_issues: list[dict] | None = None,
) -> ReviewResult:
    try:
        diff = await git_manager.get_pr_diff(pr_url)
    except Exception as e:
        return ReviewResult(body=f"Self-review skipped: {e}", issues_found=0, verdict="SKIPPED")

    oai = _openai_client_or_none()
    if oai is not None:
        body = await _review_with_openai(oai, diff[:_MAX_SINGLE_DIFF])
    elif len(diff) > _MAX_SINGLE_DIFF:
        body = await _review_large_diff(diff)
    else:
        response = await client.messages.create(
            model=settings.reviewer_model,
            max_tokens=2048,
            system=SELF_REVIEW_SYSTEM,
            messages=[{"role": "user", "content": f"## PR Diff\n```diff\n{diff}\n```\n\nReview this."}],
        )
        body = response.content[0].text.strip()

    issues = body.lower().count("[critical]") + body.lower().count("[minor]")
    verdict = "APPROVE"
    if "request_changes" in body.lower():
        verdict = "REQUEST_CHANGES"
    elif "needs_discussion" in body.lower():
        verdict = "NEEDS_DISCUSSION"

    if verdict == "APPROVE" and structured_issues:
        critical_count = sum(
            1 for i in structured_issues
            if (i.get("severity") or "").upper() in ("ERROR", "HIGH", "CRITICAL")
        )
        if critical_count > 0:
            verdict = "REQUEST_CHANGES"
            body += f"\n\n> Verdict upgraded to REQUEST_CHANGES: {critical_count} high-severity static analysis issue(s) found."

    return ReviewResult(body=body, issues_found=issues, verdict=verdict)


async def respond_to_comments(
    pr_url: str,
    git_manager: GitManager,
    poll_seconds: int = 30,
    max_polls: int = 10,
) -> None:
    seen_bodies: set[str] = set()

    for _ in range(max_polls):
        await asyncio.sleep(poll_seconds)
        comments = await git_manager.get_pr_comments(pr_url)
        new_comments = [c for c in comments if c["body"] not in seen_bodies and "nimbus" not in c["author"].lower()]

        if not new_comments:
            continue

        seen_bodies.update(c["body"] for c in new_comments)

        prompt = "Human reviewer comments on our PR:\n\n"
        for c in new_comments:
            prompt += f"**{c['author']}**: {c['body']}\n\n"
        prompt += "Draft a technical response to each comment."

        response = await client.messages.create(
            model=settings.reviewer_model,
            max_tokens=1024,
            system=COMMENT_RESPONSE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        reply = response.content[0].text.strip()
        await git_manager.post_pr_comment(pr_url, f"**Nimbus response:**\n\n{reply}")
