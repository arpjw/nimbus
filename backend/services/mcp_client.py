from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

from services.repo_config import MCPServerConfig

_log = logging.getLogger(__name__)

_CACHE: dict[str, list[dict]] = {}


async def fetch_mcp_context(
    servers: list[MCPServerConfig],
    task_id: str,
    description: str,
) -> str:
    if not servers:
        return ""

    cache_key = f"{task_id}:{','.join(s.name for s in servers)}"
    if cache_key in _CACHE:
        parts = _CACHE[cache_key]
    else:
        parts = []
        for server in servers:
            try:
                tools = await _list_tools(server)
                if not tools:
                    continue
                relevant = _pick_relevant_tools(tools, description)
                for tool_name, args in relevant:
                    result = await _call_tool(server, tool_name, args)
                    if result:
                        parts.append({"server": server.name, "tool": tool_name, "result": result})
            except Exception as exc:
                _log.warning("MCP server %s unavailable: %s", server.name, exc)
        _CACHE[cache_key] = parts

    if not parts:
        return ""

    lines = ["## MCP context"]
    for part in parts:
        lines.append(f"\n### {part['server']} / {part['tool']}\n{part['result']}")
    return "\n".join(lines)


async def _list_tools(server: MCPServerConfig) -> list[dict]:
    headers = _auth_headers(server)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            server.url,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", {}).get("tools", [])


async def _call_tool(server: MCPServerConfig, tool_name: str, arguments: dict) -> Optional[str]:
    headers = _auth_headers(server)
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            server.url,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            },
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("result", {}).get("content", [])
        if isinstance(content, list):
            return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
        return str(content) if content else None


def _auth_headers(server: MCPServerConfig) -> dict[str, str]:
    if server.auth_env:
        token = os.environ.get(server.auth_env, "")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}


def _pick_relevant_tools(tools: list[dict], description: str) -> list[tuple[str, dict]]:
    desc_lower = description.lower()
    results = []
    for tool in tools[:5]:
        name = tool.get("name", "")
        if any(kw in name.lower() for kw in ["issue", "ticket", "bug", "task", "search", "get"]):
            for word in desc_lower.split():
                if len(word) > 5 and word.replace("-", "").isalnum():
                    results.append((name, {"query": description}))
                    break
            if results and results[-1][0] == name:
                continue
    return results[:3]
