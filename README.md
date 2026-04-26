# Nimbus

**Autonomous software engineering, stratified.**

Nimbus is a multi-repository SWE agent that plans, implements, and reviews code against real codebases — entirely on its own. Run it from your terminal, VS Code, Slack, or Linear. Powered by Claude and Voyage AI.

[![PyPI version](https://badge.fury.io/py/nimbus-ai.svg)](https://pypi.org/project/nimbus-ai/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[get-nimbus.com](https://get-nimbus.com) · [docs.get-nimbus.com](https://docs.get-nimbus.com) · [api.get-nimbus.com](https://api.get-nimbus.com) · MIT License

---

## Overview

Give Nimbus a task. It handles everything: indexing your codebase, generating a grounded implementation plan, executing changes through an agentic tool-use loop, running your actual test suite, previewing the diff, opening a pull request, posting a self-review, and responding to human reviewer comments.

It runs locally on your machine or hosted on Railway — your choice.

---

## Quick start

### Install

```bash
# pip (recommended)
pip install nimbus-ai

# Homebrew (Mac)
brew tap arpjw/tap
brew install nimbus

# curl
curl -fsSL https://get-nimbus.com/install | sh
```

### Configure

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # https://console.anthropic.com
export VOYAGE_API_KEY=pa-...           # https://dash.voyageai.com
```

### Run

```bash
cd your-project
nimbus
```

That's it. The gold welcome screen appears, your repo is detected and indexed, and the REPL is ready.

### Hosted backend (no local setup)

```bash
curl -s -X POST https://api.get-nimbus.com/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"name": "my laptop", "owner_email": "you@example.com"}'

export NIMBUS_API_KEY=nk_...
nimbus run "add rate limiting to /api/upload" \
  --backend https://api.get-nimbus.com
```

Free tier: 10 tasks/month on public repos.

### Install via curl

```bash
curl -fsSL https://get-nimbus.com/install | sh
```

---

## SDKs

**Python** (`pip install nimbus-sdk`):
```python
from nimbus_sdk import NimbusClient
client = NimbusClient(api_key="nk_...")
task = client.tasks.run("add rate limiting", repo="acme/api")
task.wait()
print(task.pr_url)
```

**TypeScript** (`npm install @nimbus-ai/client`):
```typescript
import { NimbusClient } from '@nimbus-ai/client';
const client = new NimbusClient({ apiKey: 'nk_...' });
const task = await client.tasks.run({ description: 'add rate limiting', repo: 'acme/api' });
await task.wait();
console.log(task.prUrl);
```

**GitHub Actions** (see [arpjw/nimbus-action](https://github.com/arpjw/nimbus-action)):
```yaml
- uses: arpjw/nimbus-action@v1
  with:
    task: review
    api_key: ${{ secrets.NIMBUS_API_KEY }}
```

---

## Interactive terminal

Type `nimbus` with no arguments to launch the interactive REPL:

```
  ███╗   ██╗██╗███╗   ███╗██████╗ ██╗   ██╗███████╗
  ████╗  ██║██║████╗ ████║██╔══██╗██║   ██║██╔════╝
  ██╔██╗ ██║██║██╔████╔██║██████╔╝██║   ██║███████╗
  ██║╚██╗██║██║██║╚██╔╝██║██╔══██╗██║   ██║╚════██║
  ██║ ╚████║██║██║ ╚═╝ ██║██████╔╝╚██████╔╝███████║
  ╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚══════╝

  autonomous software engineering  ·  v1.1.0

  repo     github.com/acme/api
  branch   main
  indexed  847 files  ·  ready

  nimbus › _
```

Type any task description at the prompt. Nimbus plans, implements, verifies, and commits — with approval gates at each step.

### REPL commands

| Command | Description |
|---|---|
| `<task description>` | Run a task against the current repo |
| `status` | Show repo and index info |
| `undo` | Revert the last task's commit |
| `explain <file>` | Explain a file in plain English |
| `explain <file>:<start>-<end>` | Explain a specific line range |
| `help` | List all commands |
| `quit` | Exit |

### Terminal features

**Live diff streaming** — as Nimbus writes each file, the diff streams to the terminal in real time. Green additions, red deletions, line by line.

**Confidence score** — before showing the plan, Nimbus displays how confident it is based on retrieval quality and task specificity:
```
  confidence  ████████░░  82%
  retrieval   14 relevant chunks found
  ambiguity   low — task is well-scoped
```

**Session replay** — every session is recorded. Replay any past session:
```bash
nimbus replay           # replay the last session at 2x speed
nimbus replay --speed 5 # faster
```

**Ambient mode** — watch your repo and surface suggestions as you code:
```bash
nimbus watch
# nimbus  noticed 3 untested functions added to auth.py
#         want me to write tests? [y/n/s to snooze]
```

**Pair programming** — real-time suggestions on every file save:
```bash
nimbus pair
```

**Voice input** — speak your tasks:
```bash
nimbus --voice
```

**Memory viewer** — inspect and edit what Nimbus knows about your codebase:
```bash
nimbus memory           # list all memory entries
nimbus memory --delete <id>
```

**Soundtrack** — enable satisfying audio feedback in `~/.nimbus/config.toml`:
```toml
[local]
sound = true
```

---

## CLI

### Commands

```bash
# Interactive REPL (local mode)
nimbus

# One-shot task
nimbus run "migrate auth middleware to JWT"

# One-shot task via hosted backend
nimbus run "migrate auth middleware to JWT" \
  --backend https://api.get-nimbus.com \
  --api-key nk_...

# Run a built-in agent
nimbus run --agent security-audit
nimbus run --agent test-coverage --dry-run

# List all built-in agents
nimbus agents
nimbus agents --category security
nimbus agents --info security-audit

# Review any PR
nimbus review https://github.com/owner/repo/pull/42 --post

# Run from a GitHub issue
nimbus issue https://github.com/owner/repo/issues/17

# Generate tests for a file
nimbus test src/auth/middleware.py --write

# Skills
nimbus skills list
nimbus skills create --name "migrate-to-fastapi" \
  --description "..." --prompt "..."

# Explain a file
nimbus explain src/agent/orchestrator.py
nimbus explain src/auth.py:42-67

# Session replay
nimbus replay
nimbus replay --speed 5

# Ambient watching
nimbus watch
nimbus pair

# Memory management
nimbus memory
nimbus memory --delete <id>
```

### Flags (run command)

| Flag | Description |
|---|---|
| `--backend` | Backend URL (default: local) |
| `--api-key` | API key or `NIMBUS_API_KEY` env var |
| `--agent` | Run a built-in agent by name |
| `--skill` | Apply a named skill |
| `--local` | Force local execution |
| `--dry-run` | Show plan only, don't execute |
| `--yes` / `-y` | Skip approval prompts |
| `--voice` | Voice input mode |

---

## Built-in agents

Run `nimbus agents` to see all 20. Execute any with `nimbus run --agent <name>`.

### Security
| Agent | Description |
|---|---|
| `security-audit` | Scan and fix OWASP Top 10 vulnerabilities |
| `secret-scanner` | Find hardcoded secrets, move to env vars |
| `dependency-cve` | Audit and patch CVE-affected dependencies |

### Quality
| Agent | Description |
|---|---|
| `type-safety` | Add full type annotations throughout |
| `error-handling` | Wrap all external calls with typed error handling |
| `dead-code-eliminator` | Remove unused imports, variables, and functions |
| `complexity-reducer` | Refactor functions with cyclomatic complexity > 10 |
| `naming-consistency` | Fix naming convention violations across the codebase |

### Testing
| Agent | Description |
|---|---|
| `test-coverage` | Write tests targeting 80% line coverage |
| `integration-test-builder` | Generate integration tests for all API endpoints |
| `mutation-tester` | Strengthen weak tests using mutation testing |

### Documentation
| Agent | Description |
|---|---|
| `api-documenter` | Add complete OpenAPI docs to all routes |
| `readme-architect` | Rewrite the README from the actual codebase |
| `inline-documenter` | Add specific docstrings to all public functions |

### Performance
| Agent | Description |
|---|---|
| `query-optimizer` | Fix N+1 queries and missing indexes |
| `async-converter` | Convert blocking sync calls to async |

### Infrastructure
| Agent | Description |
|---|---|
| `ci-builder` | Create a complete GitHub Actions CI/CD pipeline |
| `docker-hardener` | Fix Dockerfile security and minimize image size |

### Architecture
| Agent | Description |
|---|---|
| `feature-flags` | Wrap recent features in feature flags |
| `observability-agent` | Add structured logging and tracing to the service layer |

---

## Workflow

```
TASK DESCRIPTION + REPOSITORY
          │
          ▼
    ┌─────────────┐
    │   01 CLONE  │  Isolated workspace (hosted) or CWD (local)
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  02 INDEX   │  voyage-code-2 + BM25 → ChromaDB
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  03 PLAN    │  Claude Opus + RAG + memory + active rules
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  04 APPROVE │  Confidence score shown. Approval gate (skip with --yes)
    └──────┬──────┘
           │
    ┌──────▼──────────────────────────┐
    │  05 IMPLEMENT                   │  Claude Sonnet tool-use loop
    │  live diff streams to terminal  │  Parallel workers for 6+ changes
    └──────┬──────────────────────────┘
           │
    ┌──────▼──────┐
    │  06 VERIFY  │  pytest / tsc / eslint / cargo
    └──────┬──────┘
           │
     passes? ── no ──► reformulate with error context → back to 05
           │
    ┌──────▼──────┐
    │  07 DIFF    │  Full diff shown. Approval gate (skip with --yes)
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  08 REVIEW  │  Claude Sonnet self-reviews diff → posts PR comment
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   09 PR     │  Branch pushed. PR opened. Comments monitored.
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  10 MEMORY  │  Task outcome written to per-repo memory
    └─────────────┘
```

---

## Integrations

### GitHub App

Install on any repo. Responds to:
- `/nimbus <task>` in any PR or issue comment
- `nimbus` label on any issue — fully autonomous issue-to-PR

Setup: create a GitHub App pointing to `https://api.get-nimbus.com/github/webhook`, subscribe to Issues, Issue comment, Pull request, Pull request review, Reactions.

### Slack

```
/nimbus run fix the rate limiting bug
/nimbus review https://github.com/owner/repo/pull/42
/nimbus status
```

Progress updates stream into the originating channel thread. Install: `https://api.get-nimbus.com/slack/install`.

### Linear

Assign a Linear issue to `nimbus` or apply a `nimbus` label — Nimbus opens a PR and posts the result as a Linear comment.

```bash
curl -X POST https://api.get-nimbus.com/linear/teams \
  -H "X-API-Key: nk_..." \
  -H "Content-Type: application/json" \
  -d '{"linear_team_id": "TEAM_ID", "github_repo_url": "https://github.com/owner/repo"}'
```

### VS Code / Cursor

Install the extension:
```bash
code --install-extension nimbus-0.1.0.vsix
```

Right-click any file → "Run with Nimbus..." or use `Cmd+Shift+N`. Progress streams in the editor panel. Works in both VS Code and Cursor.

### Automations

Trigger Nimbus from any event:

```bash
# PagerDuty P1 → auto-fix
POST /automations
{
  "name": "P1 auto-fix",
  "trigger_type": "webhook",
  "trigger_config": {"match": {"severity": "critical"}},
  "task_template": "Investigate and fix the incident in {{payload.service}}",
  "repo_id": "..."
}

# Weekly dependency audit
{
  "trigger_type": "cron",
  "trigger_config": {"cron": "0 9 * * 1"},
  "task_template": "Run dependency audit and update all outdated packages"
}
```

### Web dashboard

Full management UI at [get-nimbus.com/dashboard](https://get-nimbus.com/dashboard) — task history, memory viewer, API key management, automation management.

### Mobile PWA

[get-nimbus.com/app](https://get-nimbus.com/app) — trigger tasks from your phone. Install to home screen for native-like experience.

### Prism

[get-nimbus.com/prism](https://get-nimbus.com/prism) — paste a product spec or PRD and Prism breaks it into a structured, dependency-ordered sequence of Nimbus tasks. Claude Opus does the decomposition. You review and approve before anything runs.

---

## Skills system

Pre-configured agent behaviors. Reference by name instead of writing a description:

```bash
nimbus run --skill add-tests
nimbus run --skill add-openapi-docs
nimbus run --skill dependency-audit
```

**Built-in skills:** `add-tests`, `add-openapi-docs`, `dependency-audit`, `add-logging`, `add-error-handling`

**Custom skills:**
```bash
nimbus skills create \
  --name "migrate-to-fastapi" \
  --description "Migrate Django endpoints to FastAPI" \
  --prompt "Convert Django views and serializers to FastAPI route handlers..."
```

---

## Self-improving PR reviewer

After every PR, Nimbus learns from feedback:

- 👍/👎 reactions to Nimbus comments signal rules up or down
- Human reviewer comments are analyzed to extract new candidate rules  
- Rules promoted to "active" at +3 signal, disabled at -2
- Active rules injected into all future reviews for the same repo

Benchmark target: Cursor BugBot's 78% resolution rate.

---

## Architecture

```
backend/
├── agent/
│   ├── orchestrator.py          # 10-phase task lifecycle
│   ├── planner.py               # Claude Opus — RAG + rules-grounded plan
│   ├── implementer.py           # Claude Sonnet — agentic tool-use loop
│   ├── parallel_implementer.py  # Multi-worker parallel execution
│   ├── verifier.py              # Stack-aware test/lint runner
│   ├── reviewer.py              # PR self-review + comment response
│   ├── reviewer_external.py     # External PR review (rules-injected)
│   └── test_generator.py        # Test suite generation
├── services/
│   ├── embedding.py             # Voyage AI (voyage-code-2)
│   ├── vector_store.py          # ChromaDB (HNSW, cosine)
│   ├── rag.py                   # BM25 + vector + RRF hybrid retrieval
│   ├── chunker.py               # AST-aware chunking via tree-sitter
│   ├── memory.py                # Per-repo codebase memory
│   ├── review_rules.py          # Self-improving reviewer rules
│   ├── skills.py                # Skills system
│   ├── agent_library.py         # 20 built-in agents
│   └── automation_engine.py     # Webhook/cron automation dispatch
├── github_app/                  # GitHub App webhooks and handlers
├── slack_app/                   # Slack slash commands and notifications
├── linear_app/                  # Linear webhook integration
├── prism/                       # Spec-to-task decomposition
├── cli/
│   ├── main.py                  # CLI entry point — all commands
│   ├── interactive.py           # REPL loop
│   ├── local_executor.py        # Local execution engine
│   ├── renderer.py              # Rich terminal UI
│   ├── session_recorder.py      # Session recording and replay
│   ├── watcher.py               # Ambient watch mode
│   ├── pair.py                  # Pair programming mode
│   ├── voice.py                 # Voice input (Whisper)
│   ├── sounds.py                # Soundtrack
│   └── config.py                # ~/.nimbus/config.toml
└── api/routes/
    ├── tasks.py                 # Task REST + WebSocket
    ├── repos.py                 # Workspace + repo CRUD + memory
    ├── keys.py                  # API key management
    ├── skills.py                # Skills CRUD
    ├── agents.py                # Built-in agent library
    ├── automations.py           # Automations CRUD + webhook receiver
    ├── slack.py                 # Slack OAuth + slash command
    ├── linear.py                # Linear team-repo mapping
    └── prism.py                 # Prism parse + queue

frontend/
├── app/
│   ├── page.tsx                 # Landing page
│   ├── prism/                   # Prism info + tool
│   ├── dashboard/               # Task history, memory, keys, automations
│   └── app/                     # Mobile PWA
└── public/
    └── manifest.json            # PWA manifest

nimbus-vscode/                   # VS Code / Cursor extension
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required |
| `VOYAGE_API_KEY` | — | Required |
| `GITHUB_TOKEN` | — | PAT with `repo` scope |
| `GITHUB_WEBHOOK_SECRET` | — | GitHub App HMAC |
| `SLACK_BOT_TOKEN` | — | Slack bot token |
| `SLACK_SIGNING_SECRET` | — | Slack signature verification |
| `SLACK_CLIENT_ID` | — | Slack OAuth |
| `SLACK_CLIENT_SECRET` | — | Slack OAuth |
| `LINEAR_API_KEY` | — | Linear API key |
| `LINEAR_WEBHOOK_SECRET` | — | Linear HMAC |
| `REQUIRE_API_KEY` | `false` | Enable hosted API key auth |
| `PLANNER_MODEL` | `claude-opus-4-6` | Plan generation model |
| `IMPLEMENTER_MODEL` | `claude-sonnet-4-6` | Implementation model |
| `PARALLEL_THRESHOLD` | `6` | Min changes for parallel execution |
| `MAX_PARALLEL_WORKERS` | `3` | Parallel worker count |
| `FREE_TIER_MONTHLY_LIMIT` | `10` | Tasks/month on free tier |
| `CHROMA_PERSIST_DIR` | `./.chroma` | ChromaDB path |

### Local config: `~/.nimbus/config.toml`

```toml
[local]
chroma_dir = "~/.nimbus/chroma"
default_model_planner = "claude-opus-4-6"
default_model_implementer = "claude-sonnet-4-6"
editor = ""
sound = false
auto_approve_confidence = 92
pair_debounce_seconds = 3
watch_debounce_seconds = 30
replay_default_speed = 2.0
```

---

## Self-hosted setup

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
PYTHONPATH=. .venv/bin/python -m uvicorn main:app --reload --port 8000

# Frontend
cd frontend
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000' > .env.local
npm install && npm run dev

# Docker
cp .env.example .env
docker compose up --build
```

---

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Arya Somu](https://aryasomu.com) · [get-nimbus.com](https://get-nimbus.com) · [docs.get-nimbus.com](https://docs.get-nimbus.com)
