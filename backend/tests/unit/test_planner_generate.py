from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.planner import Plan, FileChange, generate_plan


def _make_response(raw_json: str) -> MagicMock:
    block = MagicMock()
    block.text = raw_json
    resp = MagicMock()
    resp.content = [block]
    return resp


def _make_llm_mock(response: MagicMock) -> MagicMock:
    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(return_value=response)
    mock_llm = MagicMock()
    mock_llm.messages = mock_messages
    return mock_llm


@pytest.mark.asyncio
async def test_generate_plan_basic():
    plan_json = json.dumps({
        "summary": "Add logging",
        "changes": [
            {"path": "app.py", "action": "modify", "description": "add logging", "rationale": "observability"},
        ],
    })
    mock_rag = MagicMock()
    mock_rag.query = AsyncMock(return_value=[])
    mock_llm = _make_llm_mock(_make_response(plan_json))

    with patch("agent.planner.instrumented_anthropic_client", return_value=mock_llm):
        plan = await generate_plan(
            task_description="Add logging to the app",
            repo_ids=["repo1"],
            rag_service=mock_rag,
            repo_file_tree="app.py\n",
        )

    assert plan.summary == "Add logging"
    assert len(plan.changes) == 1
    assert plan.changes[0].path == "app.py"


@pytest.mark.asyncio
async def test_generate_plan_with_memories():
    plan_json = json.dumps({
        "summary": "Fix bug",
        "changes": [],
    })
    mock_rag = MagicMock()
    mock_rag.query = AsyncMock(return_value=[])
    mock_llm = _make_llm_mock(_make_response(plan_json))

    memories = [{"text": "Always use type hints"}, {"text": "Follow PEP 8"}]

    with patch("agent.planner.instrumented_anthropic_client", return_value=mock_llm):
        plan = await generate_plan(
            task_description="Fix the bug",
            repo_ids=["repo1"],
            rag_service=mock_rag,
            repo_file_tree="",
            memories=memories,
        )

    assert plan.summary == "Fix bug"
    call_args = mock_llm.messages.create.call_args
    user_msg = call_args[1]["messages"][0]["content"]
    assert "Always use type hints" in user_msg


@pytest.mark.asyncio
async def test_generate_plan_markdown_fence_response():
    plan_json = json.dumps({
        "summary": "Refactor",
        "changes": [{"path": "x.py", "action": "modify", "description": "refactor", "rationale": "cleanup"}],
    })
    raw_with_fence = f"```json\n{plan_json}\n```"

    mock_rag = MagicMock()
    mock_rag.query = AsyncMock(return_value=[])
    mock_llm = _make_llm_mock(_make_response(raw_with_fence))

    with patch("agent.planner.instrumented_anthropic_client", return_value=mock_llm):
        plan = await generate_plan(
            task_description="Refactor module",
            repo_ids=["repo1"],
            rag_service=mock_rag,
            repo_file_tree="",
        )

    assert plan.summary == "Refactor"
