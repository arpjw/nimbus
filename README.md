# Nimbus

**Autonomous software engineering, stratified.**

Nimbus is a multi-repository SWE agent that plans, implements, and reviews code against real codebases — entirely on its own. Powered by Claude and Voyage AI.

[get-nimbus.com](https://get-nimbus.com) · [api.get-nimbus.com](https://api.get-nimbus.com) · MIT License

---

## Overview

Nimbus takes a task description and a target repository and handles everything: cloning the codebase, building a semantic index of all source files, generating a grounded implementation plan, executing changes through an agentic tool-use loop, running your actual test suite, previewing the diff, opening a pull request, posting a self-review, and responding to human reviewer comments.

It integrates directly into GitHub, Slack, and Linear — responding to `/nimbus` commands, triggering from issue labels, and posting progress updates wherever your team already works.

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

# Run a task using a built-in skill
nimbus run --skill add-tests \
  --backend https://api.get-nimbus.com

# Review any PR diff
nimbus review https://github.com/owner/repo/pull/42 --post

# Run a task from a GitHub issue
nimbus issue https://github.com/owner/repo/issues/17

# Generate a test suite for a file
nimbus test src/auth/middleware.py --write

# List available skills
nimbus skills list

# Create a custom skill
nimbus skills create --name "migrate-to-fastapi" \
  --description "Migrate a Django endpoint to FastAPI" \
  --prompt "Convert Django views and serializers to FastAPI route handlers..."
```

### Flags

| Flag | Description |
|---|---|
| `--backend` | Backend URL (default: `http://localhost:8000`) |
| `--api-key` | API key (or `NIMBUS_API_KEY` env var) |
| `--skill` | Run with a named skill (built-in or custom) |
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
    │  03 PLAN    │  Claude Opus retrieves context + active rules → file-level change plan
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
- **AST-aware chunking** — tree-sitter parses Python, TypeScript, and JavaScript into function and class-level chunks

### Claude Opus Planning

Before a single line is written, Claude Opus generates a structured JSON plan — a list of file-level changes with explicit rationale. Active repo-specific rules (learned from past PR feedback) are injected into the planning context automatically.

### Agentic Implementation Loop

Claude Sonnet drives a tool-use loop across `read_file`, `write_file`, `list_files`, `search_files`, `run_claude_code`, and `finish_implementation`.

### Parallel Execution

Plans with 6 or more file changes automatically split across 3 concurrent Claude Sonnet workers. Configurable via `PARALLEL_THRESHOLD` and `MAX_PARALLEL_WORKERS`.

### Persistent Codebase Memory

After every task, Nimbus writes a structured memory entry. On future tasks against the same repo, these memories are retrieved and injected into the planning prompt — making every subsequent task better informed.

### Self-Improving PR Reviewer

After opening a PR, Nimbus self-reviews its own diff and posts a structured critique. The reviewer learns from real feedback over time:

- 👍/👎 reactions to Nimbus comments signal individual rules up or down
- Human reviewer comments are analyzed to extract new candidate rules
- Rules promoted to "active" at +3 signal, disabled at -2
- Active rules injected into the reviewer system prompt on all future reviews

This mirrors Cursor BugBot's self-improving review architecture — benchmark target: 78% resolution rate.

### Skills System

Pre-configured agent behaviors for common task types. Reference a skill by name instead of describing the task from scratch.

**Built-in skills:**

| Skill | Description |
|---|---|
| `add-tests` | Write tests for all untested functions matching existing framework |
| `add-openapi-docs` | Document all route handlers with OpenAPI docstrings |
| `dependency-audit` | Identify and update stale or vulnerable dependencies |
| `add-logging` | Add structured logging to all service functions |
| `add-error-handling` | Wrap service calls with typed error handling |

Custom skills are stored per API key and available via `nimbus skills list` and `POST /skills`.

### Automations

Always-on agents triggered by external events. Register automations via `POST /automations/webhook` or the dashboard:

```bash
# Trigger on PagerDuty P1 alert
POST /automations
{
  "name": "P1 auto-fix",
  "trigger_type": "webhook",
  "trigger_config": {"match": {"severity": "critical"}},
  "task_template": "Investigate and fix the incident in {{payload.service}}",
  "repo_id": "..."
}

# Run on a schedule
{
  "trigger_type": "cron",
  "trigger_config": {"cron": "0 9 * * 1"},
  "task_template": "Run dependency audit and update all outdated packages"
}
```

Supported trigger types: `webhook` (any source), `cron`, `github_ci_fail`, PagerDuty.

### Iterative Verification

Runs your actual toolchain — pytest, tsc, eslint, cargo. On failure, error output becomes context for a new planning pass. Loops up to `MAX_IMPLEMENT_ITERATIONS` times (default: 5).

### GitHub App

Install Nimbus on any repo. It responds to:

- `/nimbus <task>` in any PR or issue comment — implements the task and opens a PR
- `nimbus` label on any issue — assigns itself, implements a fix, opens a PR

### Slack Integration

Trigger Nimbus and receive results without leaving Slack:

```
/nimbus run fix the rate limiting bug on /api/upload
/nimbus review https://github.com/owner/repo/pull/42
/nimbus status
```

Progress updates stream into the originating channel thread. Install via `/slack/install`.

### Linear Integration

Assign a Linear issue to `nimbus` or apply a `nimbus` label — Nimbus picks it up, opens a PR, and posts the result as a Linear comment. Map Linear teams to GitHub repos via `POST /linear/teams`.

### Web Dashboard

Full management UI at [get-nimbus.com/dashboard](https://get-nimbus.com/dashboard):

- **Tasks** — filterable task history with live WebSocket log replay
- **Memory** — view, add, and delete per-repo memory entries
- **Keys** — API key management and usage tracking
- **Automations** — create and manage event-driven automations

### Mobile PWA

Trigger tasks from your phone at [get-nimbus.com/app](https://get-nimbus.com/app). Install to your home screen for a native-like experience. Enter your API key once, select a repo, describe a task, and track the phase timeline in real time.

### Issue-to-PR Pipeline

Full autonomous loop: GitHub label applied → Nimbus picks it up → implements → opens PR → posts PR link back to the issue.

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

---

## Architecture

```
backend/
├── agent/
│   ├── orchestrator.py          # Full task lifecycle, WebSocket event emission
│   ├── planner.py               # Claude Opus — RAG + rules-grounded JSON plan
│   ├── implementer.py           # Claude Sonnet — agentic tool-use loop
│   ├── parallel_implementer.py  # Multi-worker parallel execution
│   ├── verifier.py              # Stack-aware test/lint runner
│   ├── reviewer.py              # PR self-review + comment response
│   ├── reviewer_external.py     # External PR review mode (rules-injected)
│   └── test_generator.py        # Test suite generation
├── services/
│   ├── embedding.py             # Voyage AI (voyage-code-2), batched async
│   ├── vector_store.py          # ChromaDB (HNSW, cosine)
│   ├── rag.py                   # BM25 + vector + RRF hybrid retrieval
│   ├── chunker.py               # AST-aware chunking via tree-sitter
│   ├── memory.py                # Persistent per-repo codebase memory
│   ├── review_rules.py          # Self-improving reviewer rules store (ChromaDB)
│   ├── skills.py                # Skills system — built-ins + custom
│   ├── automation_engine.py     # Webhook/cron automation matching and dispatch
│   └── auth.py                  # API key generation, validation, rate limiting
├── github_app/
│   ├── webhooks.py              # POST /github/webhook — HMAC validation
│   ├── handlers.py              # issue_comment, pull_request_review, reaction handlers
│   └── github.py                # GitHub API: reactions, comments
├── slack_app/
│   ├── slack_app.py             # AsyncWebClient wrapper
│   ├── handlers.py              # Slash command routing, channel-to-repo mapping
│   └── notifier.py              # Phase update notifications to Slack threads
├── linear_app/
│   ├── linear_app.py            # GraphQL client (post_comment, get_issue)
│   ├── handlers.py              # Issue assigned/labeled handlers
│   └── webhooks.py              # POST /linear/webhook — HMAC validation
├── api/
│   ├── ws.py                    # WebSocket connection manager
│   └── routes/
│       ├── tasks.py             # Task REST + WebSocket + review + test + rules endpoints
│       ├── repos.py             # Workspace + repo CRUD + memory CRUD
│       ├── keys.py              # API key management
│       ├── skills.py            # Skills CRUD
│       ├── automations.py       # Automations CRUD + public webhook receiver
│       ├── slack.py             # Slack OAuth + slash command receiver
│       └── linear.py            # Linear team-repo mapping
├── models/
│   ├── task.py                  # Task, Repo, Workspace, ChannelRepoMap, LinearTeamRepoMap
│   ├── skill.py                 # Skill SQLModel
│   ├── automation.py            # Automation SQLModel
│   └── schemas.py               # Pydantic request/response schemas
├── Dockerfile.prod
└── railway.toml

frontend/                        # Live at get-nimbus.com
├── app/
│   ├── page.tsx                 # Landing page
│   ├── dashboard/               # Full management dashboard
│   │   ├── tasks/               # Task history + live log replay
│   │   ├── memory/              # Per-repo memory viewer
│   │   ├── keys/                # API key management
│   │   └── automations/         # Automation management
│   └── app/                     # Mobile PWA
└── public/
    └── manifest.json            # PWA manifest
```

---

## Self-Hosted Setup

### Prerequisites

- Python 3.12+, Node.js 20+
- API keys: [Anthropic](https://console.anthropic.com), [Voyage AI](https://dash.voyageai.com), [GitHub](https://github.com/settings/tokens)

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env
# Fill in required env vars

PYTHONPATH=. .venv/bin/python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000' > .env.local

npm install && npm run dev
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required |
| `VOYAGE_API_KEY` | — | Required |
| `GITHUB_TOKEN` | — | Required. PAT with `repo` scope |
| `GITHUB_WEBHOOK_SECRET` | — | GitHub App webhook HMAC |
| `SLACK_BOT_TOKEN` | — | Slack App bot token (`xoxb-...`) |
| `SLACK_SIGNING_SECRET` | — | Slack request signature verification |
| `SLACK_CLIENT_ID` | — | Slack OAuth client ID |
| `SLACK_CLIENT_SECRET` | — | Slack OAuth client secret |
| `LINEAR_API_KEY` | — | Linear API key (`lin_api_...`) |
| `LINEAR_WEBHOOK_SECRET` | — | Linear webhook HMAC |
| `REQUIRE_API_KEY` | `false` | Enable hosted API key auth |
| `PLANNER_MODEL` | `claude-opus-4-6` | Plan generation model |
| `IMPLEMENTER_MODEL` | `claude-sonnet-4-6` | Implementation model |
| `REVIEWER_MODEL` | `claude-sonnet-4-6` | Self-review model |
| `EMBEDDING_MODEL` | `voyage-code-2` | Voyage embedding model |
| `MAX_IMPLEMENT_ITERATIONS` | `5` | Max implement → verify cycles |
| `PARALLEL_THRESHOLD` | `6` | Min changes to trigger parallel execution |
| `MAX_PARALLEL_WORKERS` | `3` | Parallel worker count |
| `FREE_TIER_MONTHLY_LIMIT` | `10` | Tasks/month on free API tier |
| `CHROMA_PERSIST_DIR` | `./.chroma` | ChromaDB persistence path |

---

## GitHub App Setup

1. Go to github.com/settings/apps/new
2. Set webhook URL to `https://api.get-nimbus.com/github/webhook`
3. Subscribe to: `Issues`, `Issue comment`, `Pull request`, `Pull request review`, `Reactions`
4. Install on your repos

## Slack App Setup

1. Create a Slack App at api.slack.com/apps
2. Add slash command `/nimbus` pointing to `https://api.get-nimbus.com/slack/command`
3. Enable Events API at `https://api.get-nimbus.com/slack/events`
4. Set OAuth redirect to `https://api.get-nimbus.com/slack/callback`
5. Install: `https://api.get-nimbus.com/slack/install`

## Linear Integration Setup

1. Create a Linear webhook pointing to `https://api.get-nimbus.com/linear/webhook`
2. Subscribe to `Issue` events
3. Register your team → repo mapping:

```bash
curl -X POST https://api.get-nimbus.com/linear/teams \
  -H "X-API-Key: nk_..." \
  -H "Content-Type: application/json" \
  -d '{"linear_team_id": "TEAM_ID", "github_repo_url": "https://github.com/owner/repo"}'
```

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

Built by [Arya Somu](https://aryasomu.com) · [get-nimbus.com](https://get-nimbus.com)
