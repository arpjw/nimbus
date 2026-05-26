from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_update_task_no_op_on_missing_task():
    from agent.orchestrator import _update_task
    with patch("agent.orchestrator.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get = MagicMock(return_value=None)
        mock_session_cls.return_value = mock_session
        _update_task("nonexistent-id", phase="DONE")
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_wait_for_approval_timeout():
    from agent.orchestrator import _wait_for_approval

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.blpop = AsyncMock(return_value=None)
    mock_redis.delete = AsyncMock()

    result = await _wait_for_approval(mock_redis, "test-task-id", timeout=1)
    assert result is None


@pytest.mark.asyncio
async def test_wait_for_approval_approved():
    from agent.orchestrator import _wait_for_approval

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.blpop = AsyncMock(return_value=(b"key", json.dumps({"approved": True}).encode()))
    mock_redis.delete = AsyncMock()

    result = await _wait_for_approval(mock_redis, "test-task-id", timeout=10)
    assert result is True


@pytest.mark.asyncio
async def test_wait_for_approval_rejected():
    from agent.orchestrator import _wait_for_approval

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.blpop = AsyncMock(return_value=(b"key", json.dumps({"approved": False}).encode()))
    mock_redis.delete = AsyncMock()

    result = await _wait_for_approval(mock_redis, "test-task-id", timeout=10)
    assert result is False


@pytest.mark.asyncio
async def test_emit_event_publishes_and_stores():
    from agent.orchestrator import _emit_event
    from models.task import Phase

    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_redis.rpush = AsyncMock()
    mock_redis.expire = AsyncMock()

    await _emit_event(mock_redis, "task-123", Phase.PLANNING, "test message", {"key": "value"})

    mock_redis.publish.assert_called_once()
    mock_redis.rpush.assert_called_once()
    mock_redis.expire.assert_called_once()

    channel = mock_redis.publish.call_args[0][0]
    assert "task-123" in channel

    payload_str = mock_redis.publish.call_args[0][1]
    payload = json.loads(payload_str)
    assert payload["phase"] == "planning"
    assert payload["message"] == "test message"
    assert payload["data"] == {"key": "value"}
