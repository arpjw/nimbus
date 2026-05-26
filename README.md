# Nimbus

Autonomous pull requests for your repo. Open source. Self-hostable.

Nimbus reads your codebase, plans a change, implements it, runs your tests,
and opens a PR. You review the PR like any other. No editor extension to
install, no SaaS to depend on, no $500/month.

[![PyPI version](https://badge.fury.io/py/nimbus-ai.svg)](https://pypi.org/project/nimbus-ai/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Benchmarks

| Benchmark          | Score  | Cost/task | Last run   |
|--------------------|--------|-----------|------------|
| SWE-bench Verified | --     | --        | pending    |

*Run the harness: `python -m benchmarks.swe_bench.harness --tasks 10`*

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

## How it compares

|                          | Nimbus        | Devin          | Claude Code      | Cursor       |
|--------------------------|---------------|----------------|------------------|--------------|
| Mode                     | Async PRs     | Async PRs      | Interactive CLI  | Editor       |
| Self-hostable            | Yes           | No             | N/A (CLI)        | No           |
| Open source              | MIT           | No             | No               | No           |
| GitHub-native triggers   | Yes           | Limited        | No               | No           |
| Bring your own LLM key   | Yes           | No             | Yes              | Limited      |
| Spend caps per task      | Yes           | No             | No               | No           |
| Pricing                  | Free + LLM    | $500/mo+       | Free + LLM       | $20/mo+      |

Nimbus is for the case where you want a PR opened while you sleep, against
your own infrastructure, with your own keys. Claude Code is for the case
where you want to pair with an LLM while you code. Cursor is for the case
where you want a better editor. They are not the same product.

---

## Who this is for

- Engineering teams who want to automate the toil tier of work (dependency
  bumps, security patches, doc updates, test backfilling, small refactors)
  without paying for Devin.

- Solo developers running personal projects who want a "send a task, get
  a PR" workflow against their own GitHub repos.

- Self-hosters who don't trust SaaS coding agents with their codebase.

## Who this is not for

- Greenfield product work. Nimbus is best at well-scoped tasks against an
  existing codebase, not at "build me a new app."

- Teams that need real-time pair-programming inside their editor. Use
  Cursor or Claude Code for that. They are excellent at it.

- Anyone who needs strong guarantees about correctness. Nimbus is an LLM
  agent. You review every PR before merging. This is not optional.

---

## How it works

Nimbus runs a 10-phase pipeline on every task:

```
Clone -> Index -> Plan -> [Approve] -> Implement -> Verify -> [Diff] -> Review -> PR -> Memory
```

Indexes your codebase with hybrid RAG (voyage-code-2 + BM25), plans with
Claude Opus, implements with Claude Sonnet, verifies against your real test
suite, opens a PR with a self-review attached.

---

## Terminal commands

```bash
nimbus                          # Interactive REPL -- start here
nimbus run "task description"   # Run a task directly
nimbus run --tdd "task"         # TDD mode: write failing tests first, implement to pass
nimbus run --agent <name>       # Run a built-in agent
nimbus chat                     # Ask questions about your codebase
nimbus diff [rev-range]         # Review any diff (or pipe from stdin)
nimbus diff --staged            # Review staged changes before committing
nimbus search "query"           # Semantic search over your codebase
nimbus install-hooks            # Install pre-commit review hook
nimbus uninstall-hooks          # Remove pre-commit hook
nimbus memory                   # View per-repo codebase memory
nimbus explain <file>           # Explain a file in plain English
nimbus agents                   # List built-in agents
nimbus skills list              # List available built-in skills
nimbus health                   # Codebase health scan -- 6 metrics with scores
nimbus models                   # Show configured models for each role
nimbus plugin list              # List installed CLI plugins
nimbus plugin install <pkg>     # Install a plugin from PyPI (nimbus-plugin-* namespace)
nimbus reindex <repo-id>        # Force re-index a repository
nimbus --version                # Show version
```

---

## Built-in agents

Run any agent with `nimbus run --agent <name>`:

| Category       | Agents |
|----------------|--------|
| Security       | `security-audit` `secret-scanner` `dependency-cve` |
| Quality        | `type-safety` `error-handling` `dead-code-eliminator` `complexity-reducer` `naming-consistency` |
| Testing        | `test-coverage` `integration-test-builder` `mutation-tester` |
| Docs           | `api-documenter` `readme-architect` `inline-documenter` |
| Performance    | `query-optimizer` `async-converter` |
| Infrastructure | `ci-builder` `docker-hardener` |
| Architecture   | `feature-flags` `observability-agent` |

---

## Custom models

Set per-role models in `~/.nimbus/config.toml`:

```toml
[models]
planner     = "claude-opus-4-6"
implementer = "claude-sonnet-4-6"
reviewer    = "claude-sonnet-4-6"
```

Set `OPENAI_API_KEY` and the reviewer automatically uses `gpt-4o` for a
cross-provider second opinion.

---

## Bring your own key (BYOK)

Store your own Anthropic or Voyage key so Nimbus uses it instead of billing
against your plan:

```bash
curl -X POST https://api.get-nimbus.com/keys/byok \
  -H "X-API-Key: nk_..." \
  -H "Content-Type: application/json" \
  -d '{"anthropic_key": "sk-ant-...", "voyage_key": "pa-..."}'
```

Keys are stored encrypted at rest. Monthly spend cap does not apply to BYOK
accounts.

---

## Per-repo configuration

Drop a `.nimbus.toml` in your repo root:

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

## Integrations

| Surface         | How |
|-----------------|-----|
| GitHub PRs/Issues | Comment `/nimbus` on any issue or PR |
| Slack           | `/nimbus run "task"` slash command |
| Linear          | Assign issue with `nimbus` label to auto-implement |

---

## Self-hosting

```bash
git clone https://github.com/arpjw/nimbus
cd nimbus/backend
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
uvicorn main:app --reload
```

Frontend (optional):

```bash
cd nimbus/frontend
npm install
npm run dev
```

---

## Status

| Feature                             | State       |
|-------------------------------------|-------------|
| Core pipeline (plan, implement, PR) | Stable      |
| CLI (run, diff, chat, search)       | Stable      |
| Slack / Linear integrations         | Beta        |
| Skill system (built-in agents)      | Beta        |
| Agent pipelines                     | Beta        |
| MCP server                          | Coming v1.6 |
| Skill marketplace                   | Paused      |

---

## Known limitations

**Redis + ARQ task queue (not yet implemented)**: Tasks execute in-process
on the FastAPI request handler. Under concurrent load this blocks the event
loop. Workaround: run a single uvicorn worker and limit concurrent tasks via
the rate limiter.

**Task reconciliation on restart (not yet implemented)**: If the server
restarts while a task is in-flight, the task stays in its current phase
forever. Workaround: manually PATCH the task status, or set a short timeout
in your client and retry.

---

## Changelog

### v1.5.0 -- May 2026
- BYOK -- store encrypted Anthropic/Voyage keys per account
- Incremental repository indexing via SHA256 content tracking
- Per-repo `.nimbus.toml` config (model overrides, deny paths, protected branches)
- Editable plans -- `PATCH /tasks/{id}/plan` before approval
- Sandboxed verification -- `SANDBOX_VERIFICATION=true` runs checks in Docker
- Cross-provider review -- uses `gpt-4o` when `OPENAI_API_KEY` is set
- Skill safety -- prompt injection scanning, Haiku moderation on publish
- Structured JSON logging via structlog; optional Sentry integration

### v1.4.0 -- Apr 28, 2026
- Web IDE at `get-nimbus.com/ide` (now removed -- see v1.6 roadmap for MCP)

### v1.3.0 -- Apr 27, 2026
- `nimbus run --tdd` -- TDD mode
- `nimbus health` -- codebase health scan with 6 metrics
- `nimbus models` -- show configured models per role
- CLI plugin system
- `TaskMetrics` model tracking duration, success rate, cost per task

### v1.2.0 -- Apr 26, 2026
- `nimbus chat`, `nimbus diff`, `nimbus install-hooks`, `nimbus search`
- Skill marketplace (now paused)

### v1.1.0 -- Apr 26, 2026
- Interactive terminal mode, 20 built-in agents across 7 categories
- Slack slash commands, Linear webhook integration
- GitHub OAuth -- personal dashboard, account-tied API keys

### v1.0.0 -- Apr 25, 2026
- Core 10-phase pipeline
- GitHub App with `/nimbus` comments on issues
- Self-improving PR reviewer
- Persistent per-repo memory
- Parallel implementation workers

---

## Links

- Website: [get-nimbus.com](https://get-nimbus.com)
- API docs: [api.get-nimbus.com/docs](https://api.get-nimbus.com/docs)
- Dashboard: [get-nimbus.com/dashboard](https://get-nimbus.com/dashboard)

---

Built by [Arya Somu](https://aryasomu.com) -- Monolith Systematic LLC -- MIT License
