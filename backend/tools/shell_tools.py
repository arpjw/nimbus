import asyncio
from pathlib import Path
from dataclasses import dataclass

ALLOWED_COMMANDS = {
    "python", "python3", "pytest", "npm", "npx", "node",
    "cargo", "go", "ruff", "mypy", "eslint", "tsc",
    "make", "sh", "bash",
}


@dataclass
class ShellResult:
    returncode: int
    stdout: str
    stderr: str
    passed: bool


async def run_command(
    cmd: list[str],
    cwd: Path,
    timeout: int = 120,
    env: dict | None = None,
) -> ShellResult:
    if not cmd:
        return ShellResult(returncode=1, stdout="", stderr="Empty command not allowed", passed=False)
    if cmd[0] not in ALLOWED_COMMANDS:
        return ShellResult(returncode=1, stdout="", stderr=f"Command '{cmd[0]}' not allowed", passed=False)

    import os
    merged_env = {**os.environ, **(env or {})}

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd),
            env=merged_env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        rc = proc.returncode or 0
        return ShellResult(
            returncode=rc,
            stdout=stdout.decode()[:8000],
            stderr=stderr.decode()[:4000],
            passed=rc == 0,
        )
    except asyncio.TimeoutError:
        proc.kill()
        return ShellResult(returncode=1, stdout="", stderr=f"Timed out after {timeout}s", passed=False)
    except Exception as e:
        return ShellResult(returncode=1, stdout="", stderr=str(e), passed=False)
