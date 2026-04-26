# Nimbus

**Autonomous software engineering, stratified.**

Nimbus is a multi-repository SWE agent that plans, implements, and reviews code against real codebases — entirely on its own. Powered by Claude and Voyage AI.

[get-nimbus.com](https://get-nimbus.com) · [api.get-nimbus.com](https://api.get-nimbus.com) · MIT License

---

## Overview

Nimbus takes a task description and a target repository and handles everything: cloning the codebase, building a semantic index of all source files, generating a grounded implementation plan, executing changes through an agentic tool-use loop, running your actual test suite, previewing the diff, opening a pull request, posting a self-review, and responding to human reviewer comments.

It also integrates directly into GitHub — responding to `/nimbus` commands in PR comments, auto-triggering from issue labels, and posting progress updates autonomously.

## Hosted

The backend is live at [api.get-nimbus.com](https://api.get-nimbus.com). Generate an API key and start running tasks without any local setup:

```bash
curl -s -X POST https://api.get-nimbus.com/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "my laptop", "owner_email": "you@example.com"}'
```

Free tier: 10 tasks/month on public repos. The `raw_key` is only shown once — store it securely.

---

## CLI

Install:

```bash
pip install -e ./backend
```

### Commands

```bash
# Implement a task and open a PR
nimbus run "migrate auth middleware to JWT" \
  --backend https://api.get-nimbus.com \
  --api-key nk_...

# Review any PR diff
nimbus review https://github.com/owner/repo/pull/42 --post

# Run a task from a GitHub issue
nimbus issue https://github.com/owner/repo/issues/17

# Generate a test suite for a file
nimbus test src/auth/middleware.py --write
```

Set env vars to avoid repeating flags:

```bash
export NIMBUS_API_KEY=nk_...
export NIMBUS_BACKEND=https://api.get-nimbus.com
```

### Flags

| Flag | Description |
|---|---|
| `--backend` | Backend URL (default: `http://localhost:8000`) |
| `--api-key` | API key (or `NIMBUS_API_KEY` env var) |
| `--yes` / `-y` | Skip plan and diff approval prompts |
| `--post` | Post review as a PR comment (review command) |
| `--write` | Write generated tests to disk (test command) |

---

## Workflow

```
TASK DESCRIPTION + REPOSITORY URL
          │
          ▼
    ┌─────────────┐
    │   01 CLONE  │  Isolated workspace. Feature branch.
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  02 INDEX   │  voyage-code-2 + BM25 over all source files → ChromaDB
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  03 PLAN    │  Claude Opus retrieves context → file-level change plan
    └──────┬──────┘
           │
    ┌──────▼──────┐       ┌─────────────────┐
    │  04 APPROVE │──────►│ Plan shown to   │
    │  (optional) │       │ user for review │
    └──────┬──────┘       └─────────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │  05 IMPLEMENT                        │  Claude Sonnet agentic tool-use loop
    │     read → write → verify → repeat  │  Parallel workers for 6+ file changes
    └──────┬──────────────────────────────┘
           │
    ┌──────▼──────┐
    │  06 VERIFY  │  pytest / tsc / eslint / cargo
    └──────┬──────┘
           │
     passes?──── no ────► reformulate plan with error context → back to 05
           │
          yes
           │
    ┌──────▼──────┐       ┌─────────────────┐
    │  07 DIFF    │──────►│ Diff shown to   │
    │  PREVIEW    │       │ user for review │
    └──────┬──────┘       └─────────────────┘
           │
    ┌──────▼──────┐
    │  08 REVIEW  │  Claude Sonnet self-reviews own diff → posts PR comment
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   09 PR     │  Branch pushed. PR opened. Comments monitored and addressed.
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  10 MEMORY  │  Task outcome written to per-repo memory for future tasks
    └─────────────┘
```

---

## Features

### Hybrid RAG — BM25 + Voyage AI + RRF

- **Voyage `voyage-code-2`** — embeddings purpose-built for source code
- **BM25 (Okapi)** — keyword retrieval capturing exact symbol names and identifiers
- **Reciprocal Rank Fusion** — fuses both ranked lists: `score(d) = Σ 1 / (k + rank(d))`
- **AST-aware chunking** — tree-sitter parses Python, TypeScript, and JavaScript into function and class-level chunks. Fallback to line-count chunking for other languages.

### Claude Opus Planning

Before a single line is written, Claude Opus generates a structured JSON plan — a list of file-level changes with explicit rationale. The plan is shown to the user for approval before execution begins.

### Agentic Implementation Loop

Claude Sonnet drives a tool-use loop:

| Tool | Description |
|---|---|
| `read_file` | Read any file in the workspace |
| `write_file` | Write or overwrite a file |
| `list_files` | Enumerate all source files |
| `search_files` | Regex search across the codebase |
| `run_claude_code` | Delegate to Claude Code CLI |
| `finish_implementation` | Signal completion |

### Parallel Execution

For plans with 6 or more file changes, Nimbus automatically splits the work across 3 parallel Claude Sonnet workers. Each worker handles a subset of changes simultaneously. Configurable via `PARALLEL_THRESHOLD` and `MAX_PARALLEL_WORKERS`.

### Persistent Codebase Memory

After every task, Nimbus writes a structured memory entry capturing conventions, patterns, libraries, and outcomes. On future tasks against the same repo, these memories are retrieved and injected into the planning prompt — making every subsequent task better informed.

### Iterative Verification

Runs your actual toolchain:

- **Python** — `ruff`, `mypy`, `pytest`
- **Node / TypeScript** — `tsc --noEmit`, `eslint`
- **Rust** — `cargo check`, `cargo test`
- **Go** — `go build`, `go test`

On failure, error output becomes context for a new planning pass. Loops up to `MAX_IMPLEMENT_ITERATIONS` times (default: 5).

### Diff Preview Gate

After implementation and before the PR opens, Nimbus streams the full git diff to the terminal. Lines added shown in green, removed in red. User approves or rejects before anything is pushed.

### Self-Reviewing PR Loop

After opening a PR, Nimbus:
1. Retrieves its own diff via GitHub API
2. Sends it to Claude Sonnet for structured self-critique
3. Posts the review as a PR comment (verdict: APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION)
4. Monitors for human reviewer comments and responds with technical precision

### Code Review Mode

Point Nimbus at any PR it didn't write:

```bash
nimbus review https://github.com/owner/repo/pull/42 --post
```

Retrieves the diff, produces a structured review covering correctness, edge cases, performance, security, and style. Optionally posts as a PR comment.

### Test Generation

```bash
nimbus test src/auth/middleware.py --write
```

Queries RAG for existing test conventions in the repo, detects the test framework (pytest, jest, vitest, cargo test, go test), and generates a complete test suite matching existing patterns.

### GitHub App

Install Nimbus on any repo. It then responds to:

- `/nimbus <task>` in any PR or issue comment — implements the task and opens a PR
- `nimbus` label on any issue — assigns itself, implements a fix, opens a PR, posts progress updates

### Issue-to-PR Pipeline

Full autonomous loop: label applied → Nimbus picks it up → implements → opens PR → posts PR link back to the issue. Zero human invocation after the label.

### API Key Authentication

```bash
# Generate a key
curl -X POST https://api.get-nimbus.com/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "ci", "owner_email": "you@example.com"}'

# Check usage
curl https://api.get-nimbus.com/keys/me \
  -H "X-API-Key: nk_..."
```

Free tier: 10 tasks/month. Pro tier: unlimited.

### Multi-Repository Workspaces

Group multiple repos into a workspace. Planning queries retrieve context across all repos simultaneously — enabling tasks that span service boundaries.

---

## Architecture

```
backend/
├── agent/
│   ├── orchestrator.py          # Full task lifecycle, WebSocket event emission
│   ├── planner.py               # Claude Opus — RAG-grounded JSON plan
│   ├── implementer.py           # Claude Sonnet — agentic tool-use loop
│   ├── parallel_implementer.py  # Multi-worker parallel execution
│   ├── verifier.py              # Stack-aware test/lint runner
│   ├── reviewer.py              # PR self-review + comment response
│   ├── reviewer_external.py     # External PR review mode
│   └── test_generator.py        # Test suite generation
├── services/
│   ├── embedding.py             # Voyage AI (voyage-code-2), batched async
│   ├── vector_store.py          # ChromaDB (HNSW, cosine)
│   ├── rag.py                   # BM25 + vector + RRF hybrid retrieval
│   ├── chunker.py               # AST-aware chunking via tree-sitter
│   ├── memory.py                # Persistent per-repo codebase memory
│   ├── auth.py                  # API key generation, validation, rate limiting
│   └── claude_code.py           # Claude Code CLI bridge
├── tools/
│   ├── file_tools.py            # read / write / list / search
│   ├── git_tools.py             # GitPython + PyGitHub PR creation
│   └── shell_tools.py           # Sandboxed command runner
├── github_app/
│   ├── webhooks.py              # POST /github/webhook — HMAC validation
│   ├── handlers.py              # issue_comment, issues, pull_request handlers
│   └── github.py                # GitHub API: reactions, comments
├── cli/
│   ├── main.py                  # CLI entry point — run, review, issue, test
│   ├── client.py                # Async HTTP + WebSocket client
│   └── git.py                   # Git remote detection
├── api/
│   ├── ws.py                    # WebSocket connection manager
│   └── routes/
│       ├── tasks.py             # Task REST + WebSocket + review + test endpoints
│       ├── repos.py             # Workspace + repo CRUD
│       └── keys.py              # API key management
├── models/
│   ├── task.py                  # Task, Repo, Workspace SQLModel definitions
│   └── schemas.py               # Pydantic request/response schemas
├── Dockerfile.prod              # Production Docker image
└── railway.toml                 # Railway deployment config

frontend/                        # Live at get-nimbus.com
├── app/
│   ├── page.tsx                 # Editorial landing page
│   ├── dashboard/               # Workspace and task management
│   └── task/[id]/               # Live log stream + phase timeline
└── components/
    ├── landing/                 # Hero terminal, features grid, workflow
    ├── dashboard/               # TaskCard, NewTaskModal
    └── task/                    # PhaseTimeline, LogStream
```

---

## Self-Hosted Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- API keys: [Anthropic](https://console.anthropic.com), [Voyage AI](https://dash.voyageai.com), [GitHub](https://github.com/settings/tokens)
- Claude Code CLI (optional): `npm install -g @anthropic-ai/claude-code`

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env
# Fill in ANTHROPIC_API_KEY, VOYAGE_API_KEY, GITHUB_TOKEN

PYTHONPATH=. .venv/bin/python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000' > .env.local

npm install && npm run dev
```

### Docker

```bash
cp .env.example .env
docker compose up --build
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required |
| `VOYAGE_API_KEY` | — | Required |
| `GITHUB_TOKEN` | — | Required. PAT with `repo` scope |
| `GITHUB_WEBHOOK_SECRET` | — | For GitHub App webhook HMAC validation |
| `REQUIRE_API_KEY` | `false` | Enable API key auth |
| `PLANNER_MODEL` | `claude-opus-4-6` | Plan generation model |
| `IMPLEMENTER_MODEL` | `claude-sonnet-4-6` | Implementation model |
| `REVIEWER_MODEL` | `claude-sonnet-4-6` | Self-review model |
| `EMBEDDING_MODEL` | `voyage-code-2` | Voyage embedding model |
| `MAX_IMPLEMENT_ITERATIONS` | `5` | Max implement → verify cycles |
| `RAG_TOP_K` | `20` | Chunks retrieved per query |
| `CHUNK_MAX_LINES` | `80` | Fallback chunk size |
| `PARALLEL_THRESHOLD` | `6` | Min changes to trigger parallel execution |
| `MAX_PARALLEL_WORKERS` | `3` | Parallel worker count |
| `FREE_TIER_MONTHLY_LIMIT` | `10` | Tasks/month on free API tier |
| `CHROMA_PERSIST_DIR` | `./.chroma` | ChromaDB persistence path |

---

## GitHub App Setup

1. Go to github.com/settings/apps/new
2. Set webhook URL to `https://api.get-nimbus.com/github/webhook`
3. Set webhook secret to the value of `GITHUB_WEBHOOK_SECRET`
4. Subscribe to events: `Issues`, `Issue comment`, `Pull request`
5. Install on your repos

Once installed, comment `/nimbus add rate limiting to all routes` on any issue or PR.

---

## Example Tasks

```
"Migrate authentication to JWT with refresh token support"
"Add OpenTelemetry tracing to the service layer"
"Refactor database queries from raw SQL to SQLAlchemy ORM"
"Add input validation to all POST endpoints"
"Convert the test suite from unittest to pytest"
"Add structured error responses to all API routes"
"Add a /healthz endpoint that returns {status, timestamp, version}"
```

---

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Arya Somu](https://arpjw.github.io) · [get-nimbus.com](https://get-nimbus.com)
