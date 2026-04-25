# Nimbus

**Autonomous software engineering, stratified.**

Nimbus is an enhanced SWE agent that ships production-grade pull requests against real repositories.
Built on Claude (Anthropic) + Voyage AI, with a multi-repo workspace model, hybrid RAG, Claude Code CLI integration, and a self-reviewing PR loop.

---

## What makes Nimbus different from Cirrus

| Dimension | Cirrus | Nimbus |
|---|---|---|
| LLM | OpenAI | Claude Opus (plan) + Sonnet (implement + review) |
| Embeddings | OpenAI text-embedding | Voyage `voyage-code-2` (purpose-built for code) |
| Retrieval | Vector only | BM25 + vector fusion via Reciprocal Rank Fusion |
| Chunking | Line-based | AST-aware (tree-sitter) with overlap |
| Repositories | Single | Multi-repo workspaces |
| Code execution | None | Claude Code CLI subprocess integration |
| PR review | One-shot | Self-review diff + poll and respond to human comments |
| Real-time | Polling | WebSocket streaming per task |
| Frontend | Basic | Full landing page + bento dashboard + live log view |

---

## Architecture

```
backend/
  agent/
    orchestrator.py   # Full 10-phase async state machine
    planner.py        # Claude Opus — RAG-grounded plan as JSON
    implementer.py    # Claude Sonnet — agentic tool-use loop
    verifier.py       # pytest / tsc / eslint / cargo
    reviewer.py       # PR self-review + comment response loop
  services/
    embedding.py      # Voyage AI (voyage-code-2)
    vector_store.py   # ChromaDB (HNSW, cosine)
    rag.py            # BM25 + vector + RRF hybrid retrieval
    claude_code.py    # Claude Code CLI subprocess bridge
  tools/
    file_tools.py     # read / write / list / search
    git_tools.py      # GitPython clone + PyGitHub PR creation
    shell_tools.py    # Sandboxed test runner
  api/
    ws.py             # WebSocket connection manager + queue pump
    routes/tasks.py   # REST + WebSocket task endpoints
    routes/repos.py   # Workspace + repo CRUD

frontend/
  app/
    page.tsx          # Landing page (animated terminal hero)
    dashboard/        # Workspace + task management
    task/[id]/        # Live log stream + phase timeline
  components/
    landing/          # Hero terminal, features bento, workflow
    dashboard/        # TaskCard, NewTaskModal
    task/             # PhaseTimeline, LogStream
```

---

## Workflow

```
TASK
 │
 ├─ 01 CLONE      Clone repo, create feature branch
 ├─ 02 INDEX      voyage-code-2 + BM25 over all files → ChromaDB
 ├─ 03 PLAN       Claude Opus generates JSON file-change plan via RAG
 │
 ├─ 04 IMPLEMENT  Claude Sonnet executes plan (agentic tool-use loop)
 ├─ 05 VERIFY     Run test suite / type checker / linter
 ├─ 06 FIX        Re-plan with error context → loop (max 5 iters)
 │
 ├─ 07 REVIEW     Push branch, create PR, self-review diff
 ├─ 08 PR         Post self-review as comment, monitor for replies
 └─ 09 DONE
```

---

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- `claude` CLI: `npm install -g @anthropic-ai/claude-code`
- API keys: Anthropic, Voyage AI, GitHub token

### Backend

```bash
cd backend
cp ../.env.example .env  # fill in your API keys
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
cp ../.env.example .env.local
npm install
npm run dev
```

### Docker (recommended)

```bash
cp .env.example .env  # fill in keys
docker compose up --build
```

Open http://localhost:3000

---

## Usage

### REST API

```bash
# Create workspace
curl -X POST localhost:8000/workspaces/ \
  -H "Content-Type: application/json" \
  -d '{"name": "acme-backend"}'

# Add repo to workspace
curl -X POST localhost:8000/repos/ \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "...", "url": "https://github.com/acme/api", "name": "api"}'

# Create and run task
curl -X POST localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "...", "repo_id": "...", "description": "Migrate auth to JWT"}'
```

### Python SDK (direct)

```python
from agent.orchestrator import run_task
from models.task import Task, Repo
import asyncio

task = Task(workspace_id="...", repo_id="...", description="Add rate limiting middleware")
repo = Repo(id="...", url="https://github.com/acme/api", name="api", workspace_id="...")

queue = asyncio.Queue()
asyncio.run(run_task(task, repo, queue))
```

---

## Configuration

All settings live in `backend/config.py` and are overridable via environment variables.

| Variable | Default | Description |
|---|---|---|
| `PLANNER_MODEL` | `claude-opus-4-6` | Model for plan generation |
| `IMPLEMENTER_MODEL` | `claude-sonnet-4-6` | Model for implementation |
| `EMBEDDING_MODEL` | `voyage-code-2` | Voyage embedding model |
| `MAX_IMPLEMENT_ITERATIONS` | `5` | Max implement + verify loops |
| `RAG_TOP_K` | `20` | Chunks retrieved per query |
| `CHUNK_MAX_LINES` | `80` | Lines per chunk for indexing |

---

## RAG Design

Nimbus uses a two-stage hybrid retrieval system:

1. **Voyage `voyage-code-2`** embeds every code chunk at index time and the query at runtime. Semantic similarity via cosine distance in ChromaDB (HNSW index).

2. **BM25 (Okapi)** tokenizes the same corpus and scores via term frequency. Captures exact symbol, function, and variable name matches that semantic search misses.

3. **Reciprocal Rank Fusion (RRF)** merges the two ranked lists: `score(d) = Σ 1/(k + rank(d))`. The fused ranking is robust to the weaknesses of either method alone.

For multi-repo queries, both stages run per repo and results are merged before RRF.

---

## License

MIT
