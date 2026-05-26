from __future__ import annotations

import pytest

from nimbus_core.chunker import chunk_file, _detect_language, _line_chunks


def test_detect_language_python():
    assert _detect_language("foo.py") == "python"


def test_detect_language_typescript():
    assert _detect_language("bar.ts") == "typescript"
    assert _detect_language("comp.tsx") == "typescript"


def test_detect_language_javascript():
    assert _detect_language("app.js") == "javascript"


def test_detect_language_rust():
    assert _detect_language("main.rs") == "rust"


def test_detect_language_unknown():
    assert _detect_language("README.md") == "unknown"
    assert _detect_language("Makefile") == "unknown"


@pytest.mark.asyncio
async def test_chunk_python_simple():
    content = "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    chunks = await chunk_file("test.py", content, "repo123")
    assert len(chunks) > 0
    assert all(c["repo_id"] == "repo123" for c in chunks)
    assert all(c["language"] == "python" for c in chunks)
    assert all(c["chunk_id"] for c in chunks)


@pytest.mark.asyncio
async def test_chunk_unknown_file_falls_back_to_line_chunks():
    content = "\n".join(f"line {i}" for i in range(200))
    chunks = await chunk_file("data.txt", content, "repo456")
    assert len(chunks) > 0
    assert chunks[0]["symbol_type"] == "chunk"


def test_line_chunks_basic():
    content = "\n".join(f"line {i}" for i in range(100))
    chunks = _line_chunks("test.py", content, "repo1", "python", chunk_size=30, overlap=5)
    assert len(chunks) > 1
    assert chunks[0]["start_line"] == 1


def test_line_chunks_overlap():
    content = "\n".join(f"line {i}" for i in range(50))
    chunks = _line_chunks("test.py", content, "repo1", "python", chunk_size=20, overlap=5)
    assert chunks[1]["start_line"] == 16


@pytest.mark.asyncio
async def test_chunk_ids_are_deterministic():
    content = "def foo():\n    pass\n"
    chunks1 = await chunk_file("test.py", content, "repo1")
    chunks2 = await chunk_file("test.py", content, "repo1")
    assert [c["chunk_id"] for c in chunks1] == [c["chunk_id"] for c in chunks2]


@pytest.mark.asyncio
async def test_chunk_ids_differ_by_repo():
    content = "def foo():\n    pass\n"
    chunks1 = await chunk_file("test.py", content, "repo1")
    chunks2 = await chunk_file("test.py", content, "repo2")
    assert chunks1[0]["chunk_id"] != chunks2[0]["chunk_id"]
