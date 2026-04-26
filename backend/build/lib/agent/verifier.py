"""
Verifier: detects the project type and runs appropriate checks.
Returns a structured result so the orchestrator can loop back on failure.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from tools.shell_tools import ShellResult, run_command


@dataclass
class VerificationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    output: str = ""
    checks_run: list[str] = field(default_factory=list)


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


async def verify(workspace: Path) -> VerificationResult:
    stack = _detect_stack(workspace)
    results: list[ShellResult] = []
    checks: list[str] = []

    if stack == "python":
        checks.append("ruff")
        results.append(await run_command(["ruff", "check", ".", "--exit-zero"], workspace, timeout=60))

        checks.append("mypy")
        results.append(await run_command(["mypy", ".", "--ignore-missing-imports"], workspace, timeout=90))

        if (workspace / "tests").exists() or (workspace / "test").exists():
            checks.append("pytest")
            results.append(await run_command(["pytest", "-x", "--tb=short", "-q"], workspace, timeout=120))

    elif stack == "node":
        checks.append("tsc")
        results.append(await run_command(["npx", "tsc", "--noEmit"], workspace, timeout=90))

        checks.append("eslint")
        results.append(await run_command(["npx", "eslint", ".", "--ext", ".ts,.tsx", "--max-warnings=0"], workspace, timeout=60))

    elif stack == "rust":
        checks.append("cargo check")
        results.append(await run_command(["cargo", "check"], workspace, timeout=120))

        checks.append("cargo test")
        results.append(await run_command(["cargo", "test"], workspace, timeout=180))

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
    )
