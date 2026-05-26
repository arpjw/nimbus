from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.reviewer import ReviewResult, self_review


def _make_response(text: str) -> MagicMock:
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def test_review_result_dataclass():
    r = ReviewResult(body="all good", issues_found=0, verdict="APPROVE")
    assert r.verdict == "APPROVE"
    assert r.issues_found == 0


@pytest.mark.asyncio
async def test_self_review_approve():
    mock_git = MagicMock()
    mock_git.get_pr_diff = AsyncMock(return_value="diff --git a/foo.py")
    resp = _make_response("## Self-Review\n\n**Verdict**: APPROVE\n\n**Summary**: looks good.")

    with patch("agent.reviewer.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=resp)
        result = await self_review("https://github.com/owner/repo/pull/1", mock_git)

    assert result.verdict == "APPROVE"
    assert result.issues_found == 0


@pytest.mark.asyncio
async def test_self_review_request_changes():
    mock_git = MagicMock()
    mock_git.get_pr_diff = AsyncMock(return_value="diff --git a/foo.py")
    body = "**Verdict**: request_changes\n[CRITICAL] foo.py:10 -- null deref"
    resp = _make_response(body)

    with patch("agent.reviewer.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=resp)
        result = await self_review("https://github.com/owner/repo/pull/1", mock_git)

    assert result.verdict == "REQUEST_CHANGES"
    assert result.issues_found == 1


@pytest.mark.asyncio
async def test_self_review_needs_discussion():
    mock_git = MagicMock()
    mock_git.get_pr_diff = AsyncMock(return_value="diff")
    resp = _make_response("needs_discussion about design")

    with patch("agent.reviewer.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=resp)
        result = await self_review("https://github.com/owner/repo/pull/1", mock_git)

    assert result.verdict == "NEEDS_DISCUSSION"


@pytest.mark.asyncio
async def test_self_review_diff_error_returns_skipped():
    mock_git = MagicMock()
    mock_git.get_pr_diff = AsyncMock(side_effect=RuntimeError("network error"))

    with patch("agent.reviewer.client"):
        result = await self_review("https://github.com/owner/repo/pull/1", mock_git)

    assert result.verdict == "SKIPPED"
    assert "network error" in result.body


@pytest.mark.asyncio
async def test_self_review_counts_minor_issues():
    mock_git = MagicMock()
    mock_git.get_pr_diff = AsyncMock(return_value="diff")
    body = "[CRITICAL] a\n[MINOR] b\n[MINOR] c"
    resp = _make_response(body)

    with patch("agent.reviewer.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=resp)
        result = await self_review("https://github.com/owner/repo/pull/1", mock_git)

    assert result.issues_found == 3
