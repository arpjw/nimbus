from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.planner import Plan, FileChange


def _make_message(stop_reason: str, content_blocks: list) -> MagicMock:
    msg = MagicMock()
    msg.stop_reason = stop_reason
    msg.content = content_blocks
    return msg


def _tool_use_block(name: str, tool_id: str, input_data: dict) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = name
    block.input = input_data
    return block


def _text_block(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


@pytest.fixture
def simple_plan() -> Plan:
    return Plan(
        summary="Create hello.py",
        changes=[FileChange(path="hello.py", action="create", description="Add hello fn", rationale="new")],
        raw="{}",
    )


def _make_llm_mock(side_effect=None, return_value=None):
    mock_messages = MagicMock()
    if side_effect:
        mock_messages.create = AsyncMock(side_effect=side_effect)
    else:
        mock_messages.create = AsyncMock(return_value=return_value)
    mock_llm = MagicMock()
    mock_llm.messages = mock_messages
    return mock_llm


@pytest.mark.asyncio
async def test_finish_on_first_turn(tmp_path: Path, simple_plan: Plan):
    finish_block = _tool_use_block("finish_implementation", "tu_001", {"summary": "Done"})
    finish_msg = _make_message("tool_use", [finish_block])
    mock_llm = _make_llm_mock(return_value=finish_msg)

    with patch("agent.implementer.instrumented_anthropic_client", return_value=mock_llm):
        from agent.implementer import execute_plan
        lines = []
        async for line in execute_plan(simple_plan, tmp_path):
            lines.append(line)

    assert any("[done]" in line for line in lines)
    assert mock_llm.messages.create.call_count == 1


@pytest.mark.asyncio
async def test_write_file_then_finish(tmp_path: Path, simple_plan: Plan):
    write_block = _tool_use_block("write_file", "tu_write", {"path": "hello.py", "content": "def hello(): pass\n"})
    write_msg = _make_message("tool_use", [write_block])

    finish_block = _tool_use_block("finish_implementation", "tu_finish", {"summary": "Done"})
    finish_msg = _make_message("tool_use", [finish_block])

    call_count = 0

    async def _side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return write_msg if call_count == 1 else finish_msg

    mock_llm = _make_llm_mock(side_effect=_side_effect)

    with patch("agent.implementer.instrumented_anthropic_client", return_value=mock_llm):
        from agent.implementer import execute_plan
        lines = []
        async for line in execute_plan(simple_plan, tmp_path):
            lines.append(line)

    assert (tmp_path / "hello.py").exists()
    assert any("[done]" in line for line in lines)


@pytest.mark.asyncio
async def test_end_turn_stops_loop(tmp_path: Path, simple_plan: Plan):
    end_msg = _make_message("end_turn", [_text_block("All done.")])
    mock_llm = _make_llm_mock(return_value=end_msg)

    with patch("agent.implementer.instrumented_anthropic_client", return_value=mock_llm):
        from agent.implementer import execute_plan
        lines = []
        async for line in execute_plan(simple_plan, tmp_path):
            lines.append(line)

    assert mock_llm.messages.create.call_count == 1


@pytest.mark.asyncio
async def test_tool_error_propagated(tmp_path: Path, simple_plan: Plan):
    bad_read_block = _tool_use_block("read_file", "tu_read", {"path": "../etc/passwd"})
    read_msg = _make_message("tool_use", [bad_read_block])

    finish_block = _tool_use_block("finish_implementation", "tu_f", {"summary": "Done"})
    finish_msg = _make_message("tool_use", [finish_block])

    call_count = 0

    async def _side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return read_msg if call_count == 1 else finish_msg

    mock_llm = _make_llm_mock(side_effect=_side_effect)

    with patch("agent.implementer.instrumented_anthropic_client", return_value=mock_llm):
        from agent.implementer import execute_plan
        lines = []
        async for line in execute_plan(simple_plan, tmp_path):
            lines.append(line)

    error_lines = [l for l in lines if "[error]" in l]
    assert len(error_lines) > 0
