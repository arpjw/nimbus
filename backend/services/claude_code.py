"""
Bridges the agent to the Claude Code CLI (`claude` binary) for tasks that
benefit from Claude's native shell tool-use. Falls back gracefully if the
CLI is not installed.
"""

import asyncio
import shutil
from pathlib import Path


CLAUDE_CLI = shutil.which("claude")


class ClaudeCodeUnavailable(RuntimeError):
    pass


async def run_claude_code(
    prompt: str,
    cwd: str | Path,
    timeout: int = 120,
) -> str:
    if not CLAUDE_CLI:
        raise ClaudeCodeUnavailable(
            "claude CLI not found. Install via: npm install -g @anthropic-ai/claude-code"
        )

    proc = await asyncio.create_subprocess_exec(
        CLAUDE_CLI,
        "--print",
        "--no-interactive",
        "--output-format",
        "text",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd),
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode()), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise TimeoutError(f"Claude Code timed out after {timeout}s")

    if proc.returncode != 0:
        raise RuntimeError(f"Claude Code failed: {stderr.decode()[:500]}")

    return stdout.decode()


def claude_code_available() -> bool:
    return CLAUDE_CLI is not None
