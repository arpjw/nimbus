from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.test_generator import _detect_framework, generate_tests


def test_detect_python():
    assert _detect_framework("main.py", "") == "pytest"


def test_detect_rust():
    assert _detect_framework("lib.rs", "") == "cargo test"


def test_detect_go():
    assert _detect_framework("server.go", "") == "testing package"


def test_detect_ts_defaults_jest():
    assert _detect_framework("app.ts", "") == "jest"


def test_detect_tsx_defaults_jest():
    assert _detect_framework("component.tsx", "import React") == "jest"


def test_detect_ts_vitest_by_context():
    ctx = "import { describe, it } from 'vitest'"
    assert _detect_framework("app.ts", ctx) == "vitest"


def test_detect_js_vitest_double_quote():
    ctx = 'import { expect } from "vitest"'
    assert _detect_framework("util.js", ctx) == "vitest"


def test_detect_no_extension_unknown():
    assert _detect_framework("Makefile", "") == "unknown"


def test_detect_unknown_extension():
    assert _detect_framework("data.csv", "") == "unknown"


@pytest.mark.asyncio
async def test_generate_tests_basic():
    mock_rag = MagicMock()
    mock_rag.query = AsyncMock(return_value=[])

    block = MagicMock()
    block.text = "def test_foo(): pass"
    resp = MagicMock()
    resp.content = [block]

    with patch("agent.test_generator.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=resp)
        result = await generate_tests(
            file_path="utils.py",
            content="def add(a, b): return a + b",
            repo_id="repo1",
            rag_service=mock_rag,
        )

    assert "test_foo" in result


@pytest.mark.asyncio
async def test_generate_tests_uses_rag_context():
    chunk = MagicMock()
    chunk.document = "def test_existing(): pass"
    chunk.metadata = {"file_path": "tests/test_old.py", "start_line": 1, "end_line": 5}

    mock_rag = MagicMock()
    mock_rag.query = AsyncMock(return_value=[chunk])

    block = MagicMock()
    block.text = "def test_new(): pass"
    resp = MagicMock()
    resp.content = [block]

    with patch("agent.test_generator.client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=resp)
        await generate_tests(
            file_path="app.py",
            content="x = 1",
            repo_id="repo1",
            rag_service=mock_rag,
        )

    call_args = mock_client.messages.create.call_args
    user_msg = call_args[1]["messages"][0]["content"]
    assert "test_existing" in user_msg
