# Nimbus MCP Server

Nimbus exposes an MCP server so other agents (Claude Code, Cursor agent mode, MCP-aware tools) can open PRs and search your codebase without switching tools.

## Quick start

```bash
nimbus mcp
```

This starts the MCP server over stdio. Add it to your Claude Code config:

```json
{
  "mcpServers": {
    "nimbus": {
      "command": "nimbus",
      "args": ["mcp"],
      "env": {
        "NIMBUS_API_KEY": "nk_..."
      }
    }
  }
}
```

## Tools exposed

### nimbus_create_task

Kick off a Nimbus task to implement a code change and open a PR.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| repo | string | yes | Repo name or URL (e.g. `myrepo` or `https://github.com/org/repo`) |
| description | string | yes | What to implement |
| auto_approve | bool | no | Auto-approve the plan without human input (default false) |

Returns: `{ "task_id": "...", "phase": "queued" }`

### nimbus_get_task_status

Poll a task's current state.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| task_id | string | yes | Task ID from create_task |

Returns: `{ "phase": "...", "pr_url": "...", "error": null, "confidence_score": 82.0, "estimated_cost_usd": 0.31 }`

### nimbus_search_codebase

Semantic search over a Nimbus-indexed repo.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| repo | string | yes | Repo name or URL |
| query | string | yes | Natural language query |
| top_k | int | no | Number of results (default 10) |

Returns: list of `{ "path": "...", "content": "...", "score": 0.87 }`

### nimbus_review_diff

Run Nimbus's code reviewer on any diff.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| diff | string | yes | Unified diff |
| repo_id | string | no | Repo ID for additional context |

Returns: `{ "verdict": "APPROVE|REQUEST_CHANGES|COMMENT", "body": "..." }`

## Authentication

Every MCP request requires an `X-API-Key` header matching a valid `nk_...` key. Set it via the `NIMBUS_API_KEY` environment variable when starting the MCP server.

## MCP client -- consuming external servers

Nimbus's planner can also pull context from external MCP servers (Linear, Sentry, GitHub Issues, etc.) configured per-repo in `.nimbus.toml`:

```toml
[mcp]
servers = [
  { name = "linear", url = "https://mcp.linear.app/mcp", auth_env = "LINEAR_API_KEY" },
  { name = "sentry", url = "https://mcp.sentry.io", auth_env = "SENTRY_TOKEN" },
]
```

During planning, Nimbus fetches context from each configured server and includes it in the planner's prompt. Useful for tasks that reference issue numbers or error IDs.
