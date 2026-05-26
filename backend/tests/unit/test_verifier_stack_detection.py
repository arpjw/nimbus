from __future__ import annotations

from pathlib import Path

import pytest

from agent.verifier import _detect_stack, VerificationResult


def test_detect_python_via_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").touch()
    assert _detect_stack(tmp_path) == "python"


def test_detect_python_via_requirements(tmp_path: Path):
    (tmp_path / "requirements.txt").touch()
    assert _detect_stack(tmp_path) == "python"


def test_detect_node(tmp_path: Path):
    (tmp_path / "package.json").write_text("{}")
    assert _detect_stack(tmp_path) == "node"


def test_detect_rust(tmp_path: Path):
    (tmp_path / "Cargo.toml").touch()
    assert _detect_stack(tmp_path) == "rust"


def test_detect_go(tmp_path: Path):
    (tmp_path / "go.mod").touch()
    assert _detect_stack(tmp_path) == "go"


def test_detect_unknown(tmp_path: Path):
    assert _detect_stack(tmp_path) == "unknown"


def test_python_takes_precedence_over_node(tmp_path: Path):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "package.json").write_text("{}")
    assert _detect_stack(tmp_path) == "python"


def test_verification_result_passed():
    result = VerificationResult(passed=True, checks_run=["ruff", "mypy"])
    assert result.passed is True
    assert result.errors == []


def test_verification_result_failed():
    result = VerificationResult(
        passed=False,
        errors=["ruff failed:\nE501 line too long"],
        checks_run=["ruff"],
    )
    assert result.passed is False
    assert len(result.errors) == 1
    assert "ruff" in result.errors[0]
