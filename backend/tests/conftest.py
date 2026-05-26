from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlmodel import SQLModel, create_engine, Session

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def sample_repo_path(tmp_path: Path) -> Path:
    src = FIXTURES_DIR / "sample_repo"
    import shutil
    dest = tmp_path / "sample_repo"
    shutil.copytree(src, dest)
    return dest


@pytest.fixture
def anthropic_responses() -> dict:
    with open(FIXTURES_DIR / "anthropic_responses.json") as f:
        return json.load(f)


def _make_content_block(data: dict):
    block = MagicMock()
    block.type = data["type"]
    if data["type"] == "text":
        block.text = data["text"]
    elif data["type"] == "tool_use":
        block.id = data["id"]
        block.name = data["name"]
        block.input = data["input"]
    return block


def _make_response(data: dict):
    resp = MagicMock()
    resp.id = data.get("id", "msg_test")
    resp.stop_reason = data.get("stop_reason", "end_turn")
    resp.content = [_make_content_block(b) for b in data.get("content", [])]
    usage = data.get("usage", {})
    resp.usage = MagicMock()
    resp.usage.input_tokens = usage.get("input_tokens", 0)
    resp.usage.output_tokens = usage.get("output_tokens", 0)
    return resp


@pytest.fixture
def fake_anthropic_client(anthropic_responses: dict):
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(return_value=_make_response(anthropic_responses["plan_response"]))
    return client


@pytest.fixture
def in_memory_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(in_memory_engine):
    with Session(in_memory_engine) as session:
        yield session
