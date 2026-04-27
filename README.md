# Nimbus

**Autonomous software engineering, stratified.**

[![PyPI version](https://badge.fury.io/py/nimbus-ai.svg)](https://pypi.org/project/nimbus-ai/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Nimbus plans, implements, and reviews code against real repositories — entirely on its own. From task description to merged PR.

[get-nimbus.com](https://get-nimbus.com) · [docs.get-nimbus.com](https://docs.get-nimbus.com) · [api.get-nimbus.com](https://api.get-nimbus.com)

---

## Install

```bash
# pip (recommended)
pip install nimbus-ai

# Homebrew
brew tap arpjw/tap && brew install nimbus

# curl
curl -fsSL https://get-nimbus.com/install | sh
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
Clone → Index → Plan → [Approve] → Implement → Verify → [Diff] → Review → PR → Memory
```

Every task goes from a plain English description to a merged pull request. Nimbus indexes your codebase with hybrid RAG (voyage-code-2 + BM25), plans with Claude Opus, implements with Claude Sonnet, verifies against your real test suite, and opens a PR with a self-review attached.

---

## Terminal commands

```bash
nimbus                          # Interactive REPL — start here
nimbus run "task description"   # Run a task directly
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
nimbus run --agent <name>       # Run a built-in agent
nimbus skills list              # List available skills
nimbus skills search <query>    # Search the skill marketplace
nimbus skills install <name>    # Install a community skill
nimbus skills publish           # Publish a skill to the marketplace
nimbus pipeline list            # List configured pipelines
nimbus pipeline run <name>      # Run a pipeline manually
nimbus health                   # Run codebase health scan — 6 metrics with scores
nimbus models                   # Show configured models for each role
nimbus run --tdd "task"         # TDD mode: generate failing tests first, implement to pass
nimbus plugin list              # List installed CLI plugins
nimbus plugin install <pkg>     # Install a plugin from PyPI
nimbus plugin uninstall <pkg>   # Remove a plugin
nimbus plugin run <name> <cmd>  # Run a plugin command
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

## SDKs

**Python** (`pip install nimbus-sdk`):

```python
from nimbus_sdk import NimbusClient

client = NimbusClient(api_key="nk_...")
task = client.tasks.run("add rate limiting to /api/upload", repo="acme/api")
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

---

## Custom models

Configure which model to use for each role in `~/.nimbus/config.toml`:

```toml
[models]
planner     = "claude-opus-4-6"        # default
implementer = "claude-sonnet-4-6"      # default
reviewer    = "gpt-4o"                 # OpenAI
chat        = "claude-sonnet-4-6"      # for nimbus chat

[models.ollama]
enabled  = false
base_url = "http://localhost:11434"
planner  = "deepseek-coder:33b"
```

Run `nimbus models` to see your current configuration.

Supported providers: Anthropic (default), OpenAI (`pip install openai`), Ollama (local).

---

## Plugins

Extend the Nimbus CLI with community plugins:

```bash
nimbus plugin install nimbus-plugin-jira    # adds nimbus plugin run jira <cmd>
nimbus plugin install nimbus-plugin-notion  # adds nimbus plugin run notion <cmd>
nimbus plugin list                          # show installed plugins
```

Plugins are Python packages under `nimbus-plugin-*` on PyPI. See the [example plugin](https://github.com/arpjw/nimbus-plugin-example) to build your own.

---

## GitHub Actions

```yaml
# .github/workflows/nimbus.yml
name: Nimbus Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: arpjw/nimbus-action@v1
        with:
          task: review
          api_key: ${{ secrets.NIMBUS_API_KEY }}
```

Available tasks: `review` `test-coverage` `security` `docs` or any freeform string.

---

## Chrome Extension

Install **Nimbus for GitHub** to add "Review with Nimbus" to every GitHub PR and "Implement with Nimbus" to every GitHub issue.

Load unpacked from `chrome://extensions` → Developer mode → Load unpacked → select the `nimbus-chrome` folder.

---

## Integrations

| Surface | How |
|---|---|
| GitHub PRs/Issues | Comment `/nimbus` or use the Chrome extension |
| Slack | `/nimbus run "task"` slash command |
| Linear | Assign issue with `nimbus` label → auto-implement |
| VS Code / Cursor | Right-click file → Run with Nimbus |
| GitHub Actions | `uses: arpjw/nimbus-action@v1` |

---

## Configuration

`~/.nimbus/config.toml`:

```toml
[core]
auto_approve_confidence = 92    # auto-approve plans above this confidence
default_branch = "main"
editor = "nvim"
sound = false

[hooks]
block_on = "high"               # pre-commit hook severity threshold

[models]
planner = "claude-opus-4-6"
implementer = "claude-sonnet-4-6"
reviewer = "claude-haiku-4-5-20251001"
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

Full self-hosting docs at [docs.get-nimbus.com/self-hosted/overview](https://docs.get-nimbus.com/self-hosted/overview).

---

## Ecosystem

| Package | Install |
|---|---|
| CLI | `pip install nimbus-ai` |
| Python SDK | `pip install nimbus-sdk` |
| TypeScript SDK | `npm install @nimbus-ai/client` |
| GitHub Action | `uses: arpjw/nimbus-action@v1` |
| Chrome Extension | `arpjw/nimbus-chrome` |
| VS Code Extension | `arpjw/nimbus-vscode` |
| Homebrew tap | `brew tap arpjw/tap` |

---

## Changelog

### v1.3.0 — Apr 27, 2026
- `nimbus run --tdd` — TDD mode: generates a failing test suite first, implements until all tests pass
- `nimbus health` — codebase health scan with 6 metrics (test coverage, tech debt, security, doc coverage, dep freshness, CI pass rate)
- `nimbus models` — show and configure models per role (Anthropic/OpenAI/Ollama)
- Custom model support — route each phase to any provider via `~/.nimbus/config.toml`
- CLI plugin system — `nimbus plugin install/list/run`, entry-point based discovery
- Engineering velocity dashboard at `/dashboard/analytics`
- `TaskMetrics` model tracking duration, success rate, cost per task

### v1.2.0 — Apr 26, 2026

- `nimbus chat` — conversational codebase Q&A with retrieval-backed citations
- `nimbus diff` — review any diff; pipe from stdin or pass revision range; `--exit-code` for CI
- `nimbus install-hooks` — git pre-commit hook that runs `nimbus diff --staged`
- `nimbus search` — semantic search over indexed codebase
- Architecture-aware planning — extracts repo conventions and injects them into every plan
- Automated PR description generation — structured Markdown descriptions on every PR
- Chrome Extension — "Review with Nimbus" on every GitHub PR, "Implement with Nimbus" on every issue
- Skill marketplace — `nimbus skills search/install/publish`, `/marketplace` on the web
- Agent composition pipelines — YAML-defined multi-agent workflows with scheduling
- GitHub Actions — `arpjw/nimbus-action@v1`
- Python SDK — `pip install nimbus-sdk`
- TypeScript SDK — `npm install @nimbus-ai/client`

### v1.1.0 — Apr 26, 2026

- Interactive terminal mode (`nimbus`) with live diffs, voice input, session replay
- 20 built-in agents across 7 categories
- `nimbus watch` ambient mode, `nimbus pair` per-file suggestions
- VS Code / Cursor extension
- Slack slash commands, Linear webhook integration
- Automations layer (webhook, cron, CI failure triggers)
- Prism — plain English spec to ordered task queue
- GitHub OAuth — personal dashboard, account-tied API keys

### v1.0.0 — Apr 25, 2026

- Core 10-phase pipeline
- GitHub App with `/nimbus` commands
- Self-improving PR reviewer
- Persistent per-repo memory
- Parallel implementation workers

---

## Links

- Website: [get-nimbus.com](https://get-nimbus.com)
- Docs: [docs.get-nimbus.com](https://docs.get-nimbus.com)
- Dashboard: [get-nimbus.com/dashboard](https://get-nimbus.com/dashboard)
- Marketplace: [get-nimbus.com/marketplace](https://get-nimbus.com/marketplace)
- API: [api.get-nimbus.com/docs](https://api.get-nimbus.com/docs)

---

Built by [Arya Somu](https://aryasomu.com) · Monolith Systematic LLC · MIT License
