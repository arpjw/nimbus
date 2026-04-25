<div align="center">

# Nimbus

**Autonomous software engineering, stratified.**

Nimbus is a multi-repository SWE agent that plans, implements, and reviews code against real codebases — entirely on its own. Powered by Claude and Voyage AI.

[![MIT License](https://img.shields.io/badge/license-MIT-black?style=flat-square)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-black?style=flat-square)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/next.js-14-black?style=flat-square)](https://nextjs.org)

</div>

---

## Overview

Nimbus takes a task description and a target repository and handles everything from there — cloning the codebase, building a semantic index of all source files, generating a grounded implementation plan, executing changes through an agentic tool-use loop, running your actual test suite, opening a pull request, posting a self-review of its own diff, and responding to human reviewer comments.

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
    │  02 INDEX   │  voyage-code-2 embeddings + BM25 over all source files → ChromaDB
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  03 PLAN    │  Claude Opus retrieves relevant context → file-level change plan
    └──────┬──────┘
           │
    ┌──────▼──────────────────────────────┐
    │  04 IMPLEMENT                        │  Claude Sonnet agentic tool-use loop
    │     read → write → verify → repeat  │
    └──────┬──────────────────────────────┘
           │
    ┌──────▼──────┐
    │  05 VERIFY  │  pytest / tsc / eslint / cargo
    └──────┬──────┘
           │
     passes?──── no ────► reformulate plan with error context → back to 04
           │
          yes
           │
    ┌──────▼──────┐
    │  06 REVIEW  │  Claude Sonnet reviews own diff → posts critique to PR
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   07 PR     │  Branch pushed. PR opened. Comments monitored and addressed.
    └─────────────┘
```

---

## Features

### Hybrid RAG — BM25 + Voyage AI + RRF

The retrieval layer combines two fundamentally different search methods and fuses them:

- **Voyage `voyage-code-2`** — embeddings purpose-built for source code. Understands semantic structure, function signatures, and architectural patterns at a level generic text embeddings cannot reach.
- **BM25 (Okapi)** — keyword-based retrieval that captures exact symbol names, function identifiers, and string literals that semantic search misses.
- **Reciprocal Rank Fusion** — merges both ranked lists into a single result set robust to the weaknesses of either method alone: `score(d) = Σ 1 / (k + rank(d))`.

For multi-repo queries, both stages run per repository and results are merged before fusion. The planner always retrieves from the right codebase.

### Claude Opus Planning

Before a single line is written, Claude Opus reasons over the retrieved context and produces a structured JSON plan — a list of specific file-level changes with explicit rationale for each. The implementer receives this plan and executes against it, rather than reasoning from the task description alone.

### Agentic Implementation Loop

Claude Sonnet drives a tool-use loop with access to:

| Tool | Description |
|------|-------------|
| `read_file` | Read any file in the working directory |
| `write_file` | Write or overwrite a file |
| `list_files` | Enumerate all source files |
| `search_files` | Regex search across the codebase |
| `run_claude_code` | Delegate subtasks to the Claude Code CLI |
| `finish_implementation` | Signal completion |

The loop continues until the implementer calls `finish_implementation` or the iteration limit is reached.

### Claude Code CLI Integration

For complex subtasks, the implementation loop can delegate to the `claude` CLI — a native shell tool-use agent with its own execution environment. Nimbus detects whether the CLI is installed and falls back gracefully if not.

```bash
npm install -g @anthropic-ai/claude-code
```

### Iterative Verification

Nimbus runs your actual toolchain — not a simulated check:

- **Python** — `ruff`, `mypy`, `pytest`
- **Node / TypeScript** — `tsc --noEmit`, `eslint`
- **Rust** — `cargo check`, `cargo test`
- **Go** — `go build`, `go test`

On failure, the error output becomes context for a new planning pass. The implement → verify → replan cycle runs up to `MAX_IMPLEMENT_ITERATIONS` times (default: 5).

### Self-Reviewing PR Loop

After opening a PR, Nimbus:

1. Retrieves its own diff via the GitHub API
2. Sends it to Claude Sonnet with a critical self-review prompt
3. Posts the structured critique as a PR comment (verdict: APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION)
4. Spawns a background task that polls for human reviewer comments and responds to each with technical precision

### Multi-Repository Workspaces

Repositories are organized into workspaces. A workspace can contain multiple repos — all indexed into separate ChromaDB collections under the same workspace ID. Planning queries can retrieve context across all repos in a workspace simultaneously, enabling tasks that span service boundaries.

### Real-Time WebSocket Streaming

Every phase transition, tool call, and log line streams to the frontend via WebSocket. The dashboard displays a live log stream and phase timeline for every running task.

---

## Architecture

```
backend/
├── agent/
│   ├── orchestrator.py    # 9-phase async state machine, WebSocket event emission
│   ├── planner.py         # Claude Opus — RAG-grounded JSON plan generation
│   ├── implementer.py     # Claude Sonnet — agentic tool-use execution loop
│   ├── verifier.py        # Stack-aware test/lint runner
│   └── reviewer.py        # PR self-review + human comment response loop
├── services/
│   ├── embedding.py       # Voyage AI (voyage-code-2), batched async
│   ├── vector_store.py    # ChromaDB (HNSW, cosine), per-repo collections
│   ├── rag.py             # BM25 + vector + RRF hybrid retrieval
│   └── claude_code.py     # Claude Code CLI subprocess bridge
├── tools/
│   ├── file_tools.py      # read / write / list / search (path-traversal safe)
│   ├── git_tools.py       # GitPython clone + PyGitHub PR creation
│   └── shell_tools.py     # Sandboxed command runner (allowlist-gated)
├── models/
│   ├── task.py            # Task, Repo, Workspace SQLModel definitions
│   └── schemas.py         # Pydantic request/response schemas
└── api/
    ├── ws.py              # WebSocket connection manager + queue pump
    └── routes/
        ├── tasks.py       # Task REST + WebSocket endpoints
        └── repos.py       # Workspace + repo CRUD

frontend/
├── app/
│   ├── page.tsx           # Editorial landing page
│   ├── dashboard/         # Workspace and task management
│   └── task/[id]/         # Live log stream + phase timeline
└── components/
    ├── landing/           # Hero terminal, features grid, workflow
    ├── dashboard/         # TaskCard, NewTaskModal
    └── task/              # PhaseTimeline, LogStream
```

---

## Quick Start

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

Open [http://localhost:3000](http://localhost:3000).

### Docker

```bash
cp .env.example .env   # fill in your three keys
docker compose up --build
```

---

## Usage

### Create a workspace and run a task

```bash
# 1. Create workspace
WORKSPACE=$(curl -s -X POST http://localhost:8000/workspaces/ \
  -H "Content-Type: application/json" \
  -d '{"name": "my-projects"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 2. Add a repository
REPO=$(curl -s -X POST http://localhost:8000/repos/ \
  -H "Content-Type: application/json" \
  -d "{\"workspace_id\": \"$WORKSPACE\", \"url\": \"https://github.com/you/your-repo\", \"name\": \"your-repo\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 3. Run a task
curl -s -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d "{\"workspace_id\": \"$WORKSPACE\", \"repo_id\": \"$REPO\", \"description\": \"Add rate limiting middleware to all API routes\"}" \
  | python3 -m json.tool
```

Then open `http://localhost:3000/task/{task_id}` to watch the live log stream.

### Python

```python
from agent.orchestrator import run_task
from models.task import Task, Repo
import asyncio

task = Task(
    workspace_id="...",
    repo_id="...",
    description="Migrate authentication middleware to JWT with refresh token support"
)
repo = Repo(
    id="...",
    url="https://github.com/acme/api",
    name="api",
    workspace_id="..."
)

queue = asyncio.Queue()
asyncio.run(run_task(task, repo, queue))
```

### Example tasks

```
"Update all API endpoints to use structured error responses"
"Add OpenTelemetry tracing to the service layer"
"Migrate database queries from raw SQL to SQLAlchemy ORM"
"Refactor authentication to support multiple OAuth providers"
"Add input validation and sanitization to all POST endpoints"
"Convert the test suite from unittest to pytest"
```

---

## Configuration

All settings are defined in `backend/config.py` and overridable via environment variables.

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Claude API key |
| `VOYAGE_API_KEY` | — | Required. Voyage AI key |
| `GITHUB_TOKEN` | — | Required. GitHub PAT with `repo` scope |
| `PLANNER_MODEL` | `claude-opus-4-6` | Model used for plan generation |
| `IMPLEMENTER_MODEL` | `claude-sonnet-4-6` | Model used for implementation |
| `REVIEWER_MODEL` | `claude-sonnet-4-6` | Model used for PR self-review |
| `EMBEDDING_MODEL` | `voyage-code-2` | Voyage embedding model |
| `MAX_IMPLEMENT_ITERATIONS` | `5` | Max implement → verify → replan cycles |
| `MAX_FIX_ITERATIONS` | `3` | Max targeted fix attempts per error |
| `RAG_TOP_K` | `20` | Chunks retrieved per query |
| `RAG_BM25_WEIGHT` | `0.3` | BM25 weight in RRF fusion |
| `RAG_VECTOR_WEIGHT` | `0.7` | Vector weight in RRF fusion |
| `CHUNK_MAX_LINES` | `80` | Lines per chunk at index time |
| `CHUNK_OVERLAP_LINES` | `10` | Overlap between consecutive chunks |
| `CHROMA_PERSIST_DIR` | `./.chroma` | ChromaDB persistence path |
| `WORKSPACE_BASE_DIR` | `/tmp/nimbus-workspaces` | Cloned repo working directory |

---

## RAG Design

Retrieval is the foundation of the planning step. The quality of context retrieved directly determines the quality of the implementation plan.

### Chunking

Source files are split into overlapping chunks of `CHUNK_MAX_LINES` lines with `CHUNK_OVERLAP_LINES` overlap. Each chunk is stored with metadata: `repo_id`, `file_path`, `language`, `start_line`, `end_line`, `chunk_id`.

### Embedding

All chunks are embedded with Voyage AI's `voyage-code-2` model — purpose-built for source code, significantly outperforming general-purpose text embedding models on code retrieval benchmarks. Embeddings are persisted in ChromaDB with an HNSW index using cosine similarity.

### Hybrid Retrieval

At query time:
1. The task description is embedded and queried against ChromaDB for the top-K nearest chunks by cosine similarity.
2. The same description is tokenized and scored against the BM25 corpus for the top-K chunks by term frequency.
3. Both ranked lists are merged via Reciprocal Rank Fusion into a single ranked result set.

For multi-repo workspaces, steps 1–3 run per repo and results are pooled before final ranking.

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
<sub>Built by <a href="https://arpjw.github.io">Arya Somu</a></sub>
</div>
