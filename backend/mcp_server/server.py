from __future__ import annotations

import asyncio
import logging
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp import types

from mcp_server.tools import create_task, get_task_status, search_codebase, review_diff

_log = logging.getLogger(__name__)

server = Server("nimbus")


@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="nimbus_create_task",
            description="Start a Nimbus task to implement a code change and open a PR on the given repo.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo name or URL (e.g. 'myrepo' or 'https://github.com/org/repo')"},
                    "description": {"type": "string", "description": "What to implement"},
                    "auto_approve": {"type": "boolean", "description": "Auto-approve the plan without waiting for human input", "default": False},
                },
                "required": ["repo", "description"],
            },
        ),
        types.Tool(
            name="nimbus_get_task_status",
            description="Poll the status of a Nimbus task. Returns phase, PR URL if done, and error if failed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID returned by nimbus_create_task"},
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="nimbus_search_codebase",
            description="Semantic search over a repo indexed by Nimbus. Returns relevant code chunks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo name or URL"},
                    "query": {"type": "string", "description": "Natural language search query"},
                    "top_k": {"type": "integer", "description": "Number of results to return", "default": 10},
                },
                "required": ["repo", "query"],
            },
        ),
        types.Tool(
            name="nimbus_review_diff",
            description="Run Nimbus's self-review on an arbitrary diff string.",
            inputSchema={
                "type": "object",
                "properties": {
                    "diff": {"type": "string", "description": "Unified diff to review"},
                    "repo_id": {"type": "string", "description": "Optional repo ID for context"},
                },
                "required": ["diff"],
            },
        ),
    ]


@server.call_tool()
async def _call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        if name == "nimbus_create_task":
            result = await create_task(**arguments)
        elif name == "nimbus_get_task_status":
            result = await get_task_status(**arguments)
        elif name == "nimbus_search_codebase":
            result = await search_codebase(**arguments)
        elif name == "nimbus_review_diff":
            result = await review_diff(**arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        _log.exception("Tool %s failed", name)
        result = {"error": str(exc)}

    import json
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def run_stdio() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="nimbus",
                server_version="1.5.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )
