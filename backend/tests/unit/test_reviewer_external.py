from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.reviewer_external import _parse_pr_url, _build_system_prompt, _BASE_SYSTEM_PROMPT


def test_parse_pr_url_basic():
    repo, number = _parse_pr_url("https://github.com/owner/repo/pull/42")
    assert repo == "owner/repo"
    assert number == 42


def test_parse_pr_url_trailing_slash():
    repo, number = _parse_pr_url("https://github.com/myorg/myrepo/pull/99/")
    assert repo == "myorg/myrepo"
    assert number == 99


def test_parse_pr_url_large_number():
    repo, number = _parse_pr_url("https://github.com/a/b/pull/1234")
    assert number == 1234


@pytest.mark.asyncio
async def test_build_system_prompt_no_repo_id():
    result = await _build_system_prompt(None)
    assert result == _BASE_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_build_system_prompt_no_rules():
    with patch("agent.reviewer_external._rules_service") as mock_rules:
        mock_rules.get_active_rules = AsyncMock(return_value=[])
        result = await _build_system_prompt("repo1")
    assert result == _BASE_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_build_system_prompt_with_rules():
    rules = ["Always add type hints", "Use dataclasses for DTOs"]
    with patch("agent.reviewer_external._rules_service") as mock_rules:
        mock_rules.get_active_rules = AsyncMock(return_value=rules)
        result = await _build_system_prompt("repo1")
    assert "Always add type hints" in result
    assert "Use dataclasses for DTOs" in result
    assert _BASE_SYSTEM_PROMPT in result
