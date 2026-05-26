from __future__ import annotations

import os
from pathlib import Path

import pytest
import pytest_asyncio

from tools.file_tools import read_file, write_file, _check_path


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "safe.py").write_text("x = 1\n")
    return ws


@pytest.mark.asyncio
async def test_read_safe_file(workspace: Path):
    content = await read_file(workspace, "safe.py")
    assert content == "x = 1\n"


@pytest.mark.asyncio
async def test_read_traversal_parent(workspace: Path):
    with pytest.raises(PermissionError):
        await read_file(workspace, "../etc/passwd")


@pytest.mark.asyncio
async def test_read_traversal_deep(workspace: Path):
    with pytest.raises(PermissionError):
        await read_file(workspace, "./../../etc/passwd")


@pytest.mark.asyncio
async def test_write_traversal_blocked(workspace: Path, tmp_path: Path):
    evil_dir = tmp_path / "workspace-evil"
    evil_dir.mkdir()
    with pytest.raises(PermissionError):
        await write_file(workspace, "../workspace-evil/malicious.py", "evil")


def test_prefix_match_attack_blocked(tmp_path: Path):
    root_name = "abc"
    evil_name = "abc-evil"
    workspace = tmp_path / root_name
    workspace.mkdir()
    evil_dir = tmp_path / evil_name
    evil_dir.mkdir()

    with pytest.raises(PermissionError):
        _check_path(workspace, f"../{evil_name}/file.py")


@pytest.mark.asyncio
async def test_symlink_outside_workspace_blocked(workspace: Path, tmp_path: Path):
    secret = tmp_path / "secret.txt"
    secret.write_text("secret content")
    link = workspace / "link.py"
    os.symlink(secret, link)
    with pytest.raises(PermissionError):
        await read_file(workspace, "link.py")


@pytest.mark.asyncio
async def test_write_inside_workspace_ok(workspace: Path):
    result = await write_file(workspace, "subdir/new.py", "y = 2\n")
    assert "subdir/new.py" in result
    assert (workspace / "subdir" / "new.py").read_text() == "y = 2\n"
