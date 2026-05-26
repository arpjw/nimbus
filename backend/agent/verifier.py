from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Awaitable

from tools.shell_tools import ShellResult, run_command


@dataclass
class VerificationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    output: str = ""
    checks_run: list[str] = field(default_factory=list)
    structured_issues: list[dict] = field(default_factory=list)


def _detect_stack(workspace: Path) -> str:
    if (workspace / "pyproject.toml").exists() or (workspace / "requirements.txt").exists():
        return "python"
    if (workspace / "package.json").exists():
        return "node"
    if (workspace / "Cargo.toml").exists():
        return "rust"
    if (workspace / "go.mod").exists():
        return "go"
    return "unknown"


def _parse_ruff_json(stdout: str) -> list[dict]:
    try:
        return json.loads(stdout)
    except Exception:
        return []


async def verify(workspace: Path) -> VerificationResult:
    from config import settings

    stack = _detect_stack(workspace)
    results: list[ShellResult] = []
    checks: list[str] = []
    structured: list[dict] = []

    if settings.sandbox_verification:
        from services.sandbox import run_in_sandbox

        async def _run(cmd: list[str], timeout: int = 120) -> ShellResult:
            return await run_in_sandbox(cmd, workspace, timeout=timeout, stack=stack)
    else:
        async def _run(cmd: list[str], timeout: int = 120) -> ShellResult:
            return await run_command(cmd, workspace, timeout=timeout)

    if stack == "python":
        checks.append("ruff")
        ruff_result = await _run(["ruff", "check", ".", "--output-format=json"], timeout=60)
        results.append(ruff_result)
        if ruff_result.stdout.strip():
            structured.extend(_parse_ruff_json(ruff_result.stdout))

        checks.append("mypy")
        results.append(await _run(
            ["mypy", ".", "--ignore-missing-imports", "--strict-equality", "--warn-unused-ignores"],
            timeout=90,
        ))

        if (workspace / "tests").exists() or (workspace / "test").exists():
            checks.append("pytest")
            results.append(await _run(
                ["pytest", "--maxfail=5", "--tb=short", "-q"],
                timeout=120,
            ))

    elif stack == "node":
        checks.append("tsc")
        results.append(await _run(["npx", "tsc", "--noEmit"], timeout=90))

        checks.append("eslint")
        results.append(await _run(
            ["npx", "eslint", ".", "--ext", ".ts,.tsx", "--max-warnings=0"],
            timeout=60,
        ))

    elif stack == "rust":
        checks.append("cargo check")
        results.append(await _run(["cargo", "check"], timeout=120))

        checks.append("cargo test")
        results.append(await _run(["cargo", "test"], timeout=180))

    errors: list[str] = []
    output_parts: list[str] = []
    for check, result in zip(checks, results):
        output_parts.append(f"=== {check} ===\n{result.stdout}\n{result.stderr}")
        if not result.passed:
            errors.append(f"{check} failed:\n{result.stderr[:500] or result.stdout[:500]}")

    return VerificationResult(
        passed=not errors,
        errors=errors,
        output="\n".join(output_parts)[:6000],
        checks_run=checks,
        structured_issues=structured,
    )
