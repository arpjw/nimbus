"""
Implementer: Claude Sonnet drives an agentic tool-use loop to execute the plan,
reading and writing files in the cloned workspace.
"""

import json
from pathlib import Path
from typing import AsyncGenerator

import anthropic

from agent.planner import Plan
from config import settings
from tools.file_tools import read_file, write_file, list_files, search_in_files
from services.claude_code import run_claude_code, claude_code_available

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

IMPLEMENTER_SYSTEM = """You are Nimbus Implementer — an autonomous software engineer.

You are given an implementation plan and a cloned repository. Your job is to execute
the plan precisely by reading relevant files for full context, then writing the changes.

Available tools:
- read_file: Read any file in the workspace
- write_file: Write/overwrite a file (creates parent dirs automatically)
- list_files: List all text files in the workspace
- search_files: Grep for a pattern across all files

Strategy:
1. For each planned file change, read the current file content first (if it exists)
2. Write the new/modified content
3. Read back the written file to verify correctness
4. Move to the next change

Be complete. Write full file contents, never partial stubs. Preserve existing
code style and patterns. When done with all changes, call finish_implementation.
"""

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the content of a file in the workspace",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relative file path"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file (creates or overwrites)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "List all text files in the workspace",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "search_files",
        "description": "Search for a regex pattern across all files",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "file_glob": {"type": "string", "description": "Optional glob filter e.g. '*.py'"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_claude_code",
        "description": "Delegate a complex coding subtask to Claude Code CLI (shell tool-use agent)",
        "input_schema": {
            "type": "object",
            "properties": {"prompt": {"type": "string", "description": "The coding task prompt"}},
            "required": ["prompt"],
        },
    },
    {
        "name": "finish_implementation",
        "description": "Signal that all planned changes have been applied",
        "input_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string", "description": "Brief summary of what was done"}},
            "required": ["summary"],
        },
    },
]


async def execute_plan(
    plan: Plan,
    workspace: Path,
) -> AsyncGenerator[str, None]:
    plan_text = "\n".join(
        f"- [{c.action.upper()}] {c.path}: {c.description}" for c in plan.changes
    )
    messages = [
        {
            "role": "user",
            "content": f"## Implementation Plan\n\n**Summary**: {plan.summary}\n\n**Changes**:\n{plan_text}\n\nBegin execution.",
        }
    ]

    for _ in range(50):
        response = await client.messages.create(
            model=settings.implementer_model,
            max_tokens=8192,
            system=IMPLEMENTER_SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            yield "Implementation complete (no more tool calls)."
            break

        tool_results = []
        done = False

        for block in response.content:
            if block.type == "text" and block.text.strip():
                yield f"[agent] {block.text.strip()[:200]}"

            if block.type == "tool_use":
                name, inp = block.name, block.input
                yield f"[tool] {name}({json.dumps({k: str(v)[:60] for k, v in inp.items()})})"

                try:
                    if name == "read_file":
                        content = await read_file(workspace, inp["path"])
                        result = content[:8000]
                    elif name == "write_file":
                        result = await write_file(workspace, inp["path"], inp["content"])
                    elif name == "list_files":
                        files = await list_files(workspace)
                        result = json.dumps([f["path"] for f in files])
                    elif name == "search_files":
                        hits = await search_in_files(workspace, inp["pattern"], inp.get("file_glob"))
                        result = json.dumps(hits[:50])
                    elif name == "run_claude_code":
                        if claude_code_available():
                            result = await run_claude_code(inp["prompt"], workspace)
                        else:
                            result = "Claude Code CLI not available — implement manually."
                    elif name == "finish_implementation":
                        yield f"[done] {inp.get('summary', 'Implementation finished.')}"
                        done = True
                        result = "Done."
                    else:
                        result = f"Unknown tool: {name}"
                except Exception as e:
                    result = f"Error: {e}"
                    yield f"[error] {name}: {e}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

        messages.append({"role": "user", "content": tool_results})

        if done:
            break
