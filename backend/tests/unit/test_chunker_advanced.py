from __future__ import annotations

import pytest

from nimbus_core.chunker import (
    _chunk_id,
    _line_chunks,
    _make_chunk,
    _split_if_large,
    chunk_file,
)


def test_chunk_id_is_hex():
    cid = _chunk_id("repo1", "src/main.py", 10)
    assert len(cid) == 16
    assert all(c in "0123456789abcdef" for c in cid)


def test_chunk_id_deterministic():
    assert _chunk_id("r", "f.py", 1) == _chunk_id("r", "f.py", 1)


def test_chunk_id_differs_by_line():
    assert _chunk_id("r", "f.py", 1) != _chunk_id("r", "f.py", 2)


def _make_test_chunk(start: int = 1, end: int = 10, nlines: int = 10) -> dict:
    text = "\n".join(f"line {i}" for i in range(nlines))
    return _make_chunk("repo1", "f.py", "python", start, end, text, "func", "function_definition")


def test_split_if_large_small_node_passthrough():
    chunk = _make_test_chunk(1, 10, 10)
    lines = [f"line {i}" for i in range(20)]
    result = _split_if_large(chunk, lines)
    assert result == [chunk]


def test_split_if_large_splits_over_120():
    node_lines = [f"x = {i}" for i in range(150)]
    text = "\n".join(node_lines)
    chunk = _make_chunk("repo1", "f.py", "python", 1, 150, text, "big_func", "function_definition")
    all_lines = node_lines
    result = _split_if_large(chunk, all_lines, chunk_size=40, overlap=5)
    assert len(result) > 1
    assert all(c["symbol_name"] == "big_func" for c in result)
    assert all(c["symbol_type"] == "function_definition" for c in result)


def test_line_chunks_empty_lines_skipped():
    content = "\n\n\n"
    chunks = _line_chunks("test.py", content, "repo1", "python")
    assert chunks == []


@pytest.mark.asyncio
async def test_chunk_python_class():
    content = (
        "class Foo:\n"
        "    def bar(self):\n"
        "        return 1\n"
        "\n"
        "    def baz(self):\n"
        "        return 2\n"
    )
    chunks = await chunk_file("module.py", content, "repo1")
    symbol_names = {c["symbol_name"] for c in chunks}
    assert any("Foo" in (n or "") for n in symbol_names)


@pytest.mark.asyncio
async def test_chunk_python_function():
    content = "def hello():\n    print('hi')\n"
    chunks = await chunk_file("greet.py", content, "repo1")
    assert any(c["symbol_type"] == "function_definition" for c in chunks)


@pytest.mark.asyncio
async def test_chunk_ts_function():
    content = "export function greet(name: string): string {\n  return `Hello ${name}`;\n}\n"
    chunks = await chunk_file("greet.ts", content, "repo1")
    assert len(chunks) > 0
    assert chunks[0]["language"] == "typescript"


@pytest.mark.asyncio
async def test_chunk_js_function():
    content = "function add(a, b) {\n  return a + b;\n}\n"
    chunks = await chunk_file("math.js", content, "repo1")
    assert len(chunks) > 0
    assert chunks[0]["language"] == "javascript"


@pytest.mark.asyncio
async def test_chunk_fallback_on_empty_ast():
    content = "# comment only\n"
    chunks = await chunk_file("empty.py", content, "repo1")
    assert len(chunks) > 0
