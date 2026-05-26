from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_planner_extracts_changes_from_response():
    import json
    from agent.planner import Plan, FileChange

    raw = json.dumps({
        "summary": "Fix the bug",
        "changes": [
            {"path": "src/main.py", "action": "modify", "description": "fix off-by-one", "rationale": "bug"},
        ],
    })
    changes = [FileChange(**c) for c in json.loads(raw).get("changes", [])]
    plan = Plan(summary="Fix the bug", changes=changes, raw=raw)

    assert plan.summary == "Fix the bug"
    assert len(plan.changes) == 1
    assert plan.changes[0].path == "src/main.py"
    assert plan.changes[0].action == "modify"


@pytest.mark.asyncio
async def test_orchestrator_approval_timeout_marks_failed():
    from agent.orchestrator import _wait_for_approval

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.blpop = AsyncMock(return_value=None)
    mock_redis.delete = AsyncMock()

    result = await _wait_for_approval(mock_redis, "task-xyz", timeout=1)
    assert result is None


@pytest.mark.asyncio
async def test_orchestrator_approval_rejected():
    from agent.orchestrator import _wait_for_approval

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.blpop = AsyncMock(return_value=(
        b"key",
        json.dumps({"approved": False}).encode(),
    ))
    mock_redis.delete = AsyncMock()

    result = await _wait_for_approval(mock_redis, "task-abc", timeout=10)
    assert result is False
