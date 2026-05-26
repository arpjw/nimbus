from __future__ import annotations

from pathlib import Path

import pytest

from tools.file_tools import list_files, search_in_files, _is_ignored, _is_text


@pytest.fixture
def repo_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "main.py").write_text("def main():\n    pass\n")
    (ws / "utils.ts").write_text("export function helper() {}\n")
    (ws / "README.md").write_text("# Project\n")
    sub = ws / "src"
    sub.mkdir()
    (sub / "app.py").write_text("from main import main\nmain()\n")
    ignored = ws / "node_modules"
    ignored.mkdir()
    (ignored / "package.js").write_text("module = {}")
    (ws / "data.png").write_bytes(b"\x89PNG")
    return ws


@pytest.mark.asyncio
async def test_list_files_finds_text_files(repo_workspace: Path):
    files = await list_files(repo_workspace)
    paths = {f["path"] for f in files}
    assert "main.py" in paths
    assert "utils.ts" in paths
    assert "README.md" in paths
    assert "src/app.py" in paths


@pytest.mark.asyncio
async def test_list_files_excludes_node_modules(repo_workspace: Path):
    files = await list_files(repo_workspace)
    paths = {f["path"] for f in files}
    assert not any("node_modules" in p for p in paths)


@pytest.mark.asyncio
async def test_list_files_excludes_binary(repo_workspace: Path):
    files = await list_files(repo_workspace)
    paths = {f["path"] for f in files}
    assert "data.png" not in paths


@pytest.mark.asyncio
async def test_list_files_respects_max(repo_workspace: Path):
    files = await list_files(repo_workspace, max_files=2)
    assert len(files) <= 2


@pytest.mark.asyncio
async def test_list_files_returns_metadata(repo_workspace: Path):
    files = await list_files(repo_workspace)
    for f in files:
        assert "path" in f
        assert "size" in f
        assert "extension" in f


@pytest.mark.asyncio
async def test_search_in_files_finds_pattern(repo_workspace: Path):
    results = await search_in_files(repo_workspace, "def main")
    assert len(results) > 0
    assert any("main.py" in r["file"] for r in results)


@pytest.mark.asyncio
async def test_search_in_files_returns_line_numbers(repo_workspace: Path):
    results = await search_in_files(repo_workspace, "def main")
    for r in results:
        assert r["line"] >= 1
        assert r["content"]


@pytest.mark.asyncio
async def test_search_in_files_no_match(repo_workspace: Path):
    results = await search_in_files(repo_workspace, "XYZZY_NONEXISTENT_PATTERN")
    assert results == []


@pytest.mark.asyncio
async def test_search_in_files_glob_filter(repo_workspace: Path):
    results = await search_in_files(repo_workspace, "main", file_glob="*.py")
    assert all(r["file"].endswith(".py") for r in results)


def test_is_ignored_pyc():
    assert _is_ignored(Path("module.pyc"))


def test_is_ignored_pycache():
    assert _is_ignored(Path("__pycache__"))


def test_is_ignored_git():
    assert not _is_ignored(Path("main.py"))
    from pathlib import PurePosixPath
    p = Path("/ws/.git/config")
    assert _is_ignored(p)


def test_is_text_python():
    assert _is_text(Path("foo.py"))


def test_is_text_ts():
    assert _is_text(Path("bar.ts"))


def test_is_text_unknown():
    assert not _is_text(Path("image.png"))


def test_is_text_dockerfile():
    assert _is_text(Path("Dockerfile"))
