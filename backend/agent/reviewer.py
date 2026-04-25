"""
Reviewer: performs a self-review of the PR diff and optionally responds to
human review comments, proposing follow-up fixes.
"""

import asyncio
from dataclasses import dataclass

import anthropic

from config import settings
from tools.git_tools import GitManager

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


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
- [CRITICAL/MINOR] File:line — description

**What I verified**:
- ...

Keep it concise. Flag real issues only, not style nitpicks.
"""

COMMENT_RESPONSE_SYSTEM = """You are the engineer who wrote this PR. A human reviewer
has left comments. Respond professionally and technically to each comment.
For each actionable comment, indicate whether you'll fix it (and how) or why it's correct as-is.
"""


async def self_review(pr_url: str, git_manager: GitManager) -> ReviewResult:
    try:
        diff = await git_manager.get_pr_diff(pr_url)
        diff_preview = diff[:12000]
    except Exception as e:
        return ReviewResult(body=f"Self-review skipped: {e}", issues_found=0, verdict="SKIPPED")

    response = await client.messages.create(
        model=settings.reviewer_model,
        max_tokens=2048,
        system=SELF_REVIEW_SYSTEM,
        messages=[{"role": "user", "content": f"## PR Diff\n```diff\n{diff_preview}\n```\n\nReview this."}],
    )

    body = response.content[0].text.strip()

    issues = body.lower().count("[critical]") + body.lower().count("[minor]")
    verdict = "APPROVE"
    if "request_changes" in body.lower():
        verdict = "REQUEST_CHANGES"
    elif "needs_discussion" in body.lower():
        verdict = "NEEDS_DISCUSSION"

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
