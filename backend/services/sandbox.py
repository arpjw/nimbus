from __future__ import annotations

import asyncio
import shlex
from pathlib import Path

from tools.shell_tools import ShellResult


async def run_in_sandbox(
    cmd: list[str],
    workspace: Path,
    timeout: int = 120,
    stack: str = "unknown",
) -> ShellResult:
    from config import settings

    image = _pick_image(stack, settings.sandbox_image)
    docker_cmd = [
        "docker", "run", "--rm",
        "--network=none",
        "--memory=512m",
        "--cpus=1",
        f"--workdir=/workspace",
        f"--volume={workspace.resolve()}:/workspace:rw",
        image,
        *cmd,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return ShellResult(
                returncode=1,
                stdout="",
                stderr=f"Sandbox timed out after {timeout}s",
                passed=False,
            )
        rc = proc.returncode or 0
        return ShellResult(
            returncode=rc,
            stdout=stdout_b.decode(errors="replace"),
            stderr=stderr_b.decode(errors="replace"),
            passed=rc == 0,
        )
    except FileNotFoundError:
        return ShellResult(
            returncode=1,
            stdout="",
            stderr="docker not found -- sandbox_verification requires Docker",
            passed=False,
        )


def _pick_image(stack: str, default_image: str) -> str:
    return {
        "python": "python:3.12-slim",
        "node": "node:20-slim",
        "rust": "rust:1.78-slim",
        "go": "golang:1.22-bookworm",
    }.get(stack, default_image)
