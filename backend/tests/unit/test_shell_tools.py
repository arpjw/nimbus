from __future__ import annotations

from pathlib import Path

import pytest

from tools.shell_tools import run_command, ShellResult, ALLOWED_COMMANDS


@pytest.mark.asyncio
async def test_allowed_command_runs(tmp_path: Path):
    result = await run_command(["python3", "--version"], tmp_path)
    assert result.passed is True
    assert "Python" in result.stdout or "Python" in result.stderr


@pytest.mark.asyncio
async def test_disallowed_command_blocked(tmp_path: Path):
    result = await run_command(["rm", "-rf", "/"], tmp_path)
    assert result.passed is False
    assert "not allowed" in result.stderr


@pytest.mark.asyncio
async def test_empty_command_blocked(tmp_path: Path):
    result = await run_command([], tmp_path)
    assert result.passed is False


@pytest.mark.asyncio
async def test_command_with_nonzero_exit(tmp_path: Path):
    result = await run_command(["python3", "-c", "import sys; sys.exit(1)"], tmp_path)
    assert result.passed is False
    assert result.returncode == 1


@pytest.mark.asyncio
async def test_command_stdout_captured(tmp_path: Path):
    result = await run_command(["python3", "-c", "print('hello world')"], tmp_path)
    assert result.passed is True
    assert "hello world" in result.stdout


@pytest.mark.asyncio
async def test_command_cwd_respected(tmp_path: Path):
    (tmp_path / "marker.txt").write_text("found")
    result = await run_command(
        ["python3", "-c", "import os; print(os.listdir('.'))"],
        tmp_path,
    )
    assert result.passed is True
    assert "marker.txt" in result.stdout


def test_shell_result_dataclass():
    r = ShellResult(returncode=0, stdout="ok", stderr="", passed=True)
    assert r.passed is True
    assert r.returncode == 0


def test_allowed_commands_set():
    assert "python3" in ALLOWED_COMMANDS
    assert "pytest" in ALLOWED_COMMANDS
    assert "ruff" in ALLOWED_COMMANDS
