# Nimbus

**Autonomous software engineering, stratified.**

[![PyPI version](https://badge.fury.io/py/nimbus-ai.svg)](https://pypi.org/project/nimbus-ai/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Nimbus plans, implements, and reviews code against real repositories — entirely on its own. From task description to merged PR.

[get-nimbus.com](https://get-nimbus.com) · [docs.get-nimbus.com](https://docs.get-nimbus.com) · [api.get-nimbus.com](https://api.get-nimbus.com)

---

## Status

| Feature | State |
|---|---|
| Core pipeline (plan, implement, verify, PR) | Stable |
| CLI (`nimbus run`, `nimbus diff`, `nimbus chat`, `nimbus search`) | Stable |
| Web IDE (Monaco, terminal, file tree) | Beta |
| Slack / Linear integrations | Beta |
| Skill marketplace | Beta |
| Agent pipelines | Beta |
| GitHub Actions (`arpjw/nimbus-action@v1`) | Experimental |
| Python SDK (`nimbus-sdk`) | Experimental |
| TypeScript SDK (`@nimbus-ai/client`) | Experimental |
| Chrome Extension | Experimental |
| Homebrew tap | Experimental |
| VS Code Extension | Experimental |

---

## Install

```bash
pip install nimbus-ai
```

Set your API keys:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export VOYAGE_API_KEY=pa-...
```

Then run in any git repo:

```bash
cd your-project
nimbus
```

---

## What Nimbus does

Nimbus runs a 10-phase pipeline on every task:

```
Clone -> Index -> Plan -> [Approve] -> Implement -> Verify -> [Diff] -> Review -> PR -> Memory
```

Every task goes from a plain English description to a merged pull request. Nimbus indexes your codebase with hybrid RAG (voyage-code-2 + BM25), plans with Claude Opus, implements with Claude Sonnet, verifies against your real test suite, and opens a PR with a self-review attached.

---

## Terminal commands

```bash
nimbus                          # Interactive REPL — start here
nimbus run "task description"   # Run a task directly
nimbus run --tdd "task"         # TDD mode: generate failing tests first, implement to pass
nimbus run --agent <name>       # Run a built-in agent
nimbus chat                     # Ask questions about your codebase
nimbus diff [rev-range]         # Review any diff (or pipe from stdin)
nimbus diff --staged            # Review staged changes before committing
nimbus search "query"           # Semantic search over your codebase
nimbus install-hooks            # Install pre-commit review hook
nimbus uninstall-hooks          # Remove pre-commit hook
nimbus replay                   # Replay a past session
nimbus watch                    # Ambient mode — suggestions as you code
nimbus pair                     # Per-file suggestions on every save
nimbus memory                   # View per-repo codebase memory
nimbus explain <file>           # Explain a file in plain English
nimbus agents                   # List built-in agents
nimbus skills list              # List available skills
nimbus skills search <query>    # Search the skill marketplace
nimbus skills install <name>    # Install a community skill
nimbus skills publish           # Publish a skill to the marketplace
nimbus pipeline list            # List configured pipelines
nimbus pipeline run <name>      # Run a pipeline manually
nimbus health                   # Codebase health scan — 6 metrics with scores
nimbus models                   # Show configured models for each role
nimbus plugin list              # List installed CLI plugins
nimbus plugin install <pkg>     # Install a plugin from PyPI
nimbus plugin uninstall <pkg>   # Remove a plugin
nimbus plugin run <name> <cmd>  # Run a plugin command
nimbus reindex <repo-id>        # Force re-index a repository
nimbus --version                # Show version
```

---

## Built-in agents

Run any agent with `nimbus run --agent <name>`:

| Category | Agents |
|---|---|
| Security | `security-audit` `secret-scanner` `dependency-cve` |
| Quality | `type-safety` `error-handling` `dead-code-eliminator` `complexity-reducer` `naming-consistency` |
| Testing | `test-coverage` `integration-test-builder` `mutation-tester` |
| Docs | `api-documenter` `readme-architect` `inline-documenter` |
| Performance | `query-optimizer` `async-converter` |
| Infrastructure | `ci-builder` `docker-hardener` |
| Architecture | `feature-flags` `observability-agent` |

---

## Custom models

Configure which model to use for each role in `~/.nimbus/config.toml`:

```toml
[models]
planner     = "claude-opus-4-6"
implementer = "claude-sonnet-4-6"
reviewer    = "claude-sonnet-4-6"
```

Supported providers: Anthropic (default), OpenAI (set `OPENAI_API_KEY` — reviewer uses `gpt-4o` automatically).

---

## Bring your own key (BYOK)

Store your own Anthropic or Voyage key on your account so Nimbus uses it for all tasks instead of billing against your plan:

```bash
curl -X POST https://api.get-nimbus.com/keys/byok \
  -H "X-API-Key: nk_..." \
  -H "Content-Type: application/json" \
  -d '{"anthropic_key": "sk-ant-...", "voyage_key": "pa-..."}'
```

Keys are stored encrypted at rest. When a BYOK key is configured the monthly spend cap does not apply.

---

## Plugins

Extend the Nimbus CLI with community plugins:

```bash
nimbus plugin install nimbus-plugin-jira
nimbus plugin list
nimbus plugin run jira <cmd>
```

Plugins are Python packages prefixed with `nimbus-plugin-` on PyPI.

---

## Web IDE

Open any GitHub repo in the browser — no install required:

[get-nimbus.com/ide](https://get-nimbus.com/ide)

Monaco editor, live terminal, file tree, and Nimbus chat panel. Runs on isolated containers per session.

---

## Integrations

| Surface | How |
|---|---|
| GitHub PRs/Issues | Comment `/nimbus` on any issue or PR |
| Slack | `/nimbus run "task"` slash command |
| Linear | Assign issue with `nimbus` label to auto-implement |

---

## Per-repo configuration

Drop a `.nimbus.toml` in your repo root to override defaults:

```toml
[paths]
denied = ["secrets/", "*.pem"]

[branches]
protected = ["main", "release/*"]

[models]
planner     = "claude-opus-4-7"
implementer = "claude-sonnet-4-6"

[policy]
require_human_approval = true
block_on_severity      = "error"
```

---

## Configuration

`~/.nimbus/config.toml`:

```toml
[core]
default_branch = "main"
editor = "nvim"

[hooks]
block_on = "high"               # pre-commit hook severity threshold

[models]
planner = "claude-opus-4-6"
implementer = "claude-sonnet-4-6"
reviewer = "claude-sonnet-4-6"
```

---

## Self-hosting

```bash
git clone https://github.com/arpjw/nimbus
cd nimbus

# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # add your API keys
uvicorn main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

---

## Ecosystem

| Package | Install | Status |
|---|---|---|
| CLI | `pip install nimbus-ai` | Stable |
| Web IDE | [get-nimbus.com/ide](https://get-nimbus.com/ide) | Beta |
| Python SDK | `pip install nimbus-sdk` | Experimental |
| TypeScript SDK | `npm install @nimbus-ai/client` | Experimental |
| GitHub Action | `uses: arpjw/nimbus-action@v1` | Experimental |
| Chrome Extension | `arpjw/nimbus-chrome` | Experimental |
| VS Code Extension | `arpjw/nimbus-vscode` | Experimental |

---

## Known limitations

**Redis + ARQ task queue (not yet implemented)**: Tasks currently execute in-process on the FastAPI request handler. Under concurrent load this blocks the event loop. A proper ARQ worker queue with Redis pub/sub is planned but not yet shipped. Workaround: run a single uvicorn worker and limit concurrent tasks via the rate limiter.

**Task reconciliation on restart (not yet implemented)**: If the server restarts while a task is in-flight, the task stays in its current phase forever. There is no reconciler that resets stuck tasks to `FAILED` on startup. Workaround: manually PATCH the task status, or set a short timeout in your client and retry.

---

## Changelog

### v1.5.0 — May 2026
- BYOK (bring your own key) — store encrypted Anthropic/Voyage keys per account; spend cap bypassed when BYOK is active
- Incremental repository indexing — skip unchanged files via SHA256 content tracking
- Per-repo `.nimbus.toml` config — override models, deny paths, protect branches
- Editable plans — `PATCH /tasks/{id}/plan` lets users modify file changes before approval
- Sandboxed verification — `SANDBOX_VERIFICATION=true` runs ruff/pytest/mypy inside Docker
- Cross-provider self-review — reviewer uses `gpt-4o` when `OPENAI_API_KEY` is set
- Static analysis override — APPROVE verdict upgraded to REQUEST_CHANGES when ruff reports errors
- Skill safety — prompt injection scanning and Haiku moderation on skill publish
- Structured JSON logging via structlog; optional Sentry integration

### v1.4.0 — Apr 28, 2026
- Web IDE at `get-nimbus.com/ide` — Monaco editor, xterm.js terminal, isolated containers per session
- Nimbus chat panel in the IDE

### v1.3.0 — Apr 27, 2026
- `nimbus run --tdd` — TDD mode: generate failing tests first, implement to pass
- `nimbus health` — codebase health scan with 6 metrics
- `nimbus models` — show configured models per role
- CLI plugin system — `nimbus plugin install/list/run`, entry-point based discovery
- `TaskMetrics` model tracking duration, success rate, cost per task

### v1.2.0 — Apr 26, 2026
- `nimbus chat` — conversational codebase Q&A with retrieval-backed citations
- `nimbus diff` — review any diff; pipe from stdin or pass revision range; `--exit-code` for CI
- `nimbus install-hooks` — git pre-commit hook that runs `nimbus diff --staged`
- `nimbus search` — semantic search over indexed codebase
- Skill marketplace — `nimbus skills search/install/publish`
- Agent composition pipelines

### v1.1.0 — Apr 26, 2026
- Interactive terminal mode (`nimbus`) with live diffs, session replay
- 20 built-in agents across 7 categories
- `nimbus watch` ambient mode, `nimbus pair` per-file suggestions
- Slack slash commands, Linear webhook integration
- GitHub OAuth — personal dashboard, account-tied API keys

### v1.0.0 — Apr 25, 2026
- Core 10-phase pipeline
- GitHub App with `/nimbus` comments on issues
- Self-improving PR reviewer
- Persistent per-repo memory
- Parallel implementation workers

---

## Links

- Website: [get-nimbus.com](https://get-nimbus.com)
- Docs: [docs.get-nimbus.com](https://docs.get-nimbus.com)
- Dashboard: [get-nimbus.com/dashboard](https://get-nimbus.com/dashboard)
- API: [api.get-nimbus.com/docs](https://api.get-nimbus.com/docs)

---

Built by [Arya Somu](https://aryasomu.com) · Monolith Systematic LLC · MIT License
