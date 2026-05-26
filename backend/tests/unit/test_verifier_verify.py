from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agent.verifier import verify, VerificationResult
from tools.shell_tools import ShellResult


def _passed(stdout: str = "", stderr: str = "") -> ShellResult:
    return ShellResult(stdout=stdout, stderr=stderr, returncode=0, passed=True)


def _failed(stdout: str = "", stderr: str = "") -> ShellResult:
    return ShellResult(stdout=stdout, stderr=stderr, returncode=1, passed=False)


@pytest.mark.asyncio
async def test_verify_python_all_pass(tmp_path: Path):
    (tmp_path / "pyproject.toml").touch()
    with patch("agent.verifier.run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = _passed()
        result = await verify(tmp_path)
    assert result.passed is True
    assert "ruff" in result.checks_run
    assert "mypy" in result.checks_run


@pytest.mark.asyncio
async def test_verify_python_ruff_fail(tmp_path: Path):
    (tmp_path / "requirements.txt").touch()
    with patch("agent.verifier.run_command", new_callable=AsyncMock) as mock_run:
        def _side_effect(cmd, *args, **kwargs):
            if "ruff" in cmd:
                return _failed(stderr="E501 line too long")
            return _passed()
        mock_run.side_effect = _side_effect
        result = await verify(tmp_path)
    assert result.passed is False
    assert any("ruff" in e for e in result.errors)


@pytest.mark.asyncio
async def test_verify_python_runs_pytest_when_tests_exist(tmp_path: Path):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "tests").mkdir()
    with patch("agent.verifier.run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = _passed()
        result = await verify(tmp_path)
    assert "pytest" in result.checks_run


@pytest.mark.asyncio
async def test_verify_python_skips_pytest_when_no_tests(tmp_path: Path):
    (tmp_path / "pyproject.toml").touch()
    with patch("agent.verifier.run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = _passed()
        result = await verify(tmp_path)
    assert "pytest" not in result.checks_run


@pytest.mark.asyncio
async def test_verify_node(tmp_path: Path):
    (tmp_path / "package.json").write_text("{}")
    with patch("agent.verifier.run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = _passed()
        result = await verify(tmp_path)
    assert "tsc" in result.checks_run
    assert "eslint" in result.checks_run


@pytest.mark.asyncio
async def test_verify_rust(tmp_path: Path):
    (tmp_path / "Cargo.toml").touch()
    with patch("agent.verifier.run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = _passed()
        result = await verify(tmp_path)
    assert "cargo check" in result.checks_run
    assert "cargo test" in result.checks_run


@pytest.mark.asyncio
async def test_verify_unknown_stack(tmp_path: Path):
    result = await verify(tmp_path)
    assert result.passed is True
    assert result.checks_run == []


@pytest.mark.asyncio
async def test_verify_error_aggregation(tmp_path: Path):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "tests").mkdir()
    with patch("agent.verifier.run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = _failed(stderr="some error")
        result = await verify(tmp_path)
    assert result.passed is False
    assert len(result.errors) == len(result.checks_run)
