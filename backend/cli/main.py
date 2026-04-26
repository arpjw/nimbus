import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import typer
from colorama import Fore, Style, init

from cli.client import NimbusClient
from cli.git import get_git_remote

init(autoreset=True)

app = typer.Typer(
    name="nimbus",
    help="Nimbus autonomous SWE agent CLI",
    add_completion=False,
    invoke_without_command=True,
)

skills_app = typer.Typer(help="Manage skills")
app.add_typer(skills_app, name="skills")

_PHASE_COLOR = {
    "queued": Fore.WHITE,
    "cloning": Fore.CYAN,
    "indexing": Fore.CYAN,
    "planning": Fore.YELLOW,
    "awaiting_approval": Fore.YELLOW,
    "awaiting_diff_approval": Fore.YELLOW,
    "implementing": Fore.BLUE,
    "verifying": Fore.MAGENTA,
    "fixing": Fore.YELLOW,
    "reviewing": Fore.BLUE,
    "pr_creation": Fore.CYAN,
    "cleanup": Fore.CYAN,
    "done": Fore.GREEN,
    "failed": Fore.RED,
}

_TERMINAL_PHASES = {"done", "failed"}


def _print_plan_table(changes: list[dict]) -> None:
    if not changes:
        return
    headers = ("ACTION", "FILE", "DESCRIPTION")
    rows = [
        (c.get("action", "").upper(), c.get("path", ""), c.get("description", ""))
        for c in changes
    ]
    col_widths = [
        max(len(headers[i]), max((len(r[i]) for r in rows), default=0))
        for i in range(3)
    ]
    col_widths[2] = min(col_widths[2], 60)
    sep = "  ".join("-" * w for w in col_widths)
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(Style.BRIGHT + header_line + Style.RESET_ALL)
    print(sep)
    for row in rows:
        desc = row[2][:60]
        print("  ".join(cell.ljust(w) for cell, w in zip((row[0], row[1], desc), col_widths)))


def _print_diff(diff: str) -> None:
    print(Style.DIM + "-" * 60 + Style.RESET_ALL)
    for line in diff.splitlines():
        if line.startswith("@@"):
            print(Fore.CYAN + line + Style.RESET_ALL)
        elif line.startswith("+") and not line.startswith("+++"):
            print(Fore.GREEN + line + Style.RESET_ALL)
        elif line.startswith("-") and not line.startswith("---"):
            print(Fore.RED + line + Style.RESET_ALL)
        else:
            print(line)
    print(Style.DIM + "-" * 60 + Style.RESET_ALL)


def _fmt_event(event: dict) -> str:
    phase = event.get("phase", "")
    message = event.get("message", "")
    ts_raw = event.get("ts", "")
    try:
        ts = datetime.fromisoformat(ts_raw).astimezone(timezone.utc).strftime("%H:%M:%S")
    except Exception:
        ts = (ts_raw[:8] if ts_raw else "        ")
    color = _PHASE_COLOR.get(phase, Fore.WHITE)
    ts_str = Style.DIM + ts + Style.RESET_ALL
    phase_str = color + Style.BRIGHT + f"{phase:<14}" + Style.RESET_ALL
    return f"  {ts_str}  {phase_str}  {message}"


_VERDICT_COLOR = {
    "APPROVE": Fore.GREEN,
    "REQUEST_CHANGES": Fore.RED,
    "NEEDS_DISCUSSION": Fore.YELLOW,
}


def version_callback(value: bool):
    if value:
        typer.echo("nimbus 1.1.0")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def default(
    ctx: typer.Context,
    voice: bool = typer.Option(False, "--voice", help="Use voice input for task description"),
    version: bool = typer.Option(False, "--version", "-v", callback=version_callback, is_eager=True, help="Show version"),
):
    if ctx.invoked_subcommand is None:
        from cli.config import check_first_run
        if not check_first_run():
            raise typer.Exit()
        from cli.interactive import NimbusREPL
        repl = NimbusREPL(Path.cwd(), voice_mode=voice)
        asyncio.run(repl.start())


@app.command()
def chat():
    """Ask questions about your codebase conversationally."""
    from cli.interactive import NimbusREPL
    repl = NimbusREPL(Path.cwd())
    asyncio.run(repl._init_executor())
    asyncio.run(repl.do_chat())


@app.command()
def diff(
    rev_range: str = typer.Argument(None, help="Git revision range e.g. HEAD~3..HEAD or main..feature"),
    staged: bool = typer.Option(False, "--staged", help="Review staged changes"),
    severity: str = typer.Option("medium", "--severity", help="Minimum severity to show: low|medium|high"),
    exit_code: bool = typer.Option(False, "--exit-code", help="Exit 1 if issues found (for CI use)"),
):
    """Review any diff -- pipe from stdin or pass a revision range."""
    import subprocess, anthropic
    from cli.renderer import console, GOLD, GREEN, RED, FAINT
    from rich.panel import Panel
    from rich import box

    diff_text = ""
    if not sys.stdin.isatty():
        diff_text = sys.stdin.read()
    elif staged:
        result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, cwd=str(Path.cwd()))
        diff_text = result.stdout
    elif rev_range:
        result = subprocess.run(["git", "diff", rev_range], capture_output=True, text=True, cwd=str(Path.cwd()))
        diff_text = result.stdout
    else:
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, cwd=str(Path.cwd()))
        diff_text = result.stdout

    if not diff_text.strip():
        console.print(f"  [{FAINT}]no diff to review[/{FAINT}]")
        raise typer.Exit()

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Review this code diff. For each issue found, format as:
SEVERITY: high|medium|low
FILE: filename:line
ISSUE: one sentence description
SUGGESTION: one sentence fix

Then end with:
OVERALL: excellent|good|needs-work|major-issues
SUMMARY: one sentence

Diff:
{diff_text[:6000]}"""
        }]
    )

    text = response.content[0].text
    lines = text.strip().split("\n")
    issues = []
    current = {}
    overall = "good"
    summary = ""

    for line in lines:
        if line.startswith("SEVERITY:"):
            if current:
                issues.append(current)
            current = {"severity": line.split(":", 1)[1].strip()}
        elif line.startswith("FILE:") and current:
            current["file"] = line.split(":", 1)[1].strip()
        elif line.startswith("ISSUE:") and current:
            current["issue"] = line.split(":", 1)[1].strip()
        elif line.startswith("SUGGESTION:") and current:
            current["suggestion"] = line.split(":", 1)[1].strip()
        elif line.startswith("OVERALL:"):
            if current:
                issues.append(current)
                current = {}
            overall = line.split(":", 1)[1].strip()
        elif line.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()

    severity_map = {"low": 1, "medium": 2, "high": 3}
    min_sev = severity_map.get(severity, 2)
    filtered = [i for i in issues if severity_map.get(i.get("severity", "low"), 1) >= min_sev]

    console.print()
    if filtered:
        for issue in filtered:
            sev = issue.get("severity", "medium")
            icon = f"[{RED}]✗[/{RED}]" if sev == "high" else f"[yellow]⚠[/yellow]" if sev == "medium" else f"[{FAINT}]·[/{FAINT}]"
            console.print(f"  {icon}  [{FAINT}]{issue.get('file','')}[/{FAINT}]")
            console.print(f"     {issue.get('issue','')}")
            if issue.get("suggestion"):
                console.print(f"     [{FAINT}]{issue.get('suggestion','')}[/{FAINT}]")
            console.print()

    overall_color = GREEN if overall in ("excellent", "good") else RED
    console.print(f"  [{FAINT}]overall[/{FAINT}]  [{overall_color}]{overall}[/{overall_color}]" + (f"  [{FAINT}]{summary}[/{FAINT}]" if summary else ""))
    console.print()

    if exit_code and filtered:
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Natural language search query"),
    top_k: int = typer.Option(8, "--top-k", "-k", help="Number of results to return"),
    open_file: bool = typer.Option(False, "--open", help="Open top result in $EDITOR"),
):
    """Semantic search over your indexed codebase."""
    from cli.local_executor import LocalExecutor
    from cli.renderer import console, GOLD, FAINT
    from services.embedding import EmbeddingService

    async def _search():
        executor = LocalExecutor(Path.cwd())

        try:
            collection = executor.chroma.get_collection(executor.collection_name)
        except Exception:
            console.print(f"\n  [{FAINT}]codebase not indexed — run nimbus first to index[/{FAINT}]\n")
            return

        embedder = EmbeddingService()
        embeddings = await embedder.embed_queries([query])

        count = collection.count()
        if count == 0:
            console.print(f"\n  [{FAINT}]no results found[/{FAINT}]\n")
            return

        results = collection.query(
            query_embeddings=embeddings,
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"]
        )

        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        if not docs:
            console.print(f"\n  [{FAINT}]no results found[/{FAINT}]\n")
            return

        console.print(f"\n  [{GOLD}]nimbus search[/{GOLD}]  [{FAINT}]{query}[/{FAINT}]\n")
        console.print(f"  {len(docs)} results\n")

        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            path = meta.get("path", "unknown")
            try:
                rel = str(Path(path).relative_to(Path.cwd()))
            except Exception:
                rel = path
            score = round(1 - dist, 2) if dist else 0
            prefix = "├─" if i < len(docs) - 1 else "└─"
            summary = doc.strip().split("\n")[0][:80] if doc else ""
            console.print(f"  {prefix} [{GOLD}]{rel}[/{GOLD}]  [{FAINT}]score {score}[/{FAINT}]")
            if summary:
                console.print(f"     [{FAINT}]{summary}[/{FAINT}]")
            console.print()

        if open_file and metas:
            import subprocess as _sp, os
            first_path = metas[0].get("path", "")
            editor = os.environ.get("EDITOR", "nano")
            if first_path and Path(first_path).exists():
                _sp.run([editor, first_path])

    asyncio.run(_search())


@app.command(name="install-hooks")
def install_hooks(
    severity: str = typer.Option("high", "--severity", help="Block on: high|medium|low"),
):
    """Install Nimbus pre-commit hook in the current git repo."""
    from cli.renderer import console, GREEN, RED, FAINT

    repo = Path.cwd()
    hooks_dir = repo / ".git" / "hooks"

    if not hooks_dir.exists():
        console.print(f"  [{RED}]not a git repo[/{RED}]")
        raise typer.Exit(1)

    hook_path = hooks_dir / "pre-commit"
    hook_script = f"""#!/bin/sh
# Nimbus pre-commit hook
# Installed by: nimbus install-hooks

NIMBUS_BIN=$(which nimbus 2>/dev/null || echo "nimbus")

if ! command -v nimbus >/dev/null 2>&1; then
  exit 0
fi

$NIMBUS_BIN diff --staged --severity={severity} --exit-code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo ""
  echo "  Nimbus found issues. Fix them or run:"
  echo "  git commit --no-verify  (to skip Nimbus review)"
  echo ""
fi

exit $EXIT_CODE
"""

    hook_path.write_text(hook_script)
    hook_path.chmod(0o755)

    console.print(f"\n  [{GREEN}]✓[/{GREEN}] Nimbus pre-commit hook installed")
    console.print(f"  [{FAINT}]blocking on severity: {severity}[/{FAINT}]")
    console.print(f"  [{FAINT}]skip with: git commit --no-verify[/{FAINT}]")
    console.print(f"  [{FAINT}]remove with: nimbus uninstall-hooks[/{FAINT}]\n")


@app.command(name="uninstall-hooks")
def uninstall_hooks():
    """Remove Nimbus pre-commit hook from the current git repo."""
    from cli.renderer import console, GREEN, RED, FAINT

    hook_path = Path.cwd() / ".git" / "hooks" / "pre-commit"
    if hook_path.exists() and "Nimbus pre-commit hook" in hook_path.read_text():
        hook_path.unlink()
        console.print(f"\n  [{GREEN}]✓[/{GREEN}] Nimbus pre-commit hook removed\n")
    else:
        console.print(f"\n  [{FAINT}]no Nimbus hook found[/{FAINT}]\n")


@app.command()
def agents(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    info: Optional[str] = typer.Option(None, "--info", help="Show full info for a named agent"),
):
    """List all built-in agents, or get info on a specific one."""
    from services.agent_library import list_agents, get_agent
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from cli.renderer import console, GOLD, FAINT, GREEN

    if info:
        agent = get_agent(info)
        if not agent:
            console.print(f"  [{FAINT}]agent not found: {info}[/{FAINT}]")
            raise typer.Exit()
        content = (
            f"[bold white]{agent.name}[/bold white]  [{FAINT}]{agent.category}[/{FAINT}]\n\n"
            f"{agent.full_description}\n\n"
            f"[{FAINT}]retrieval   [/][white]{agent.retrieval_strategy}[/white]\n"
            f"[{FAINT}]estimated   [/][white]{agent.estimated_prs}[/white]\n"
            f"[{FAINT}]verify      [/][white]{agent.verification_command[:60]}[/white]"
        )
        console.print(Panel(content, border_style=FAINT, box=box.ROUNDED))
        return

    agents_list = list_agents(category)
    console.print()

    by_cat: dict = {}
    for a in agents_list:
        by_cat.setdefault(a.category, []).append(a)

    for cat, cat_agents in by_cat.items():
        console.print(f"  [{FAINT}]{cat.upper()}[/{FAINT}]")
        table = Table.grid(padding=(0, 3))
        table.add_column(style=f"bold {GOLD}", width=26)
        table.add_column(style=FAINT)
        for a in cat_agents:
            table.add_row(a.name, a.description)
        console.print("  ", table)
        console.print()

    console.print(f"  [{FAINT}]run: nimbus run --agent <name>[/{FAINT}]")
    console.print(f"  [{FAINT}]info: nimbus agents --info <name>[/{FAINT}]\n")


@app.command()
def run(
    task: Optional[str] = typer.Argument(None, help='Task description, e.g. "fix the login bug"'),
    agent: Optional[str] = typer.Option(None, "--agent", help="Run a built-in agent by name"),
    backend: str = typer.Option("http://localhost:8000", help="Nimbus backend URL"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    api_key: Optional[str] = typer.Option(None, help="Nimbus API key (defaults to NIMBUS_API_KEY)"),
    skill: Optional[str] = typer.Option(None, help="Apply a named skill to this task"),
):
    """Submit a task to the Nimbus backend agent."""
    if agent and not task:
        from services.agent_library import get_agent as _get_agent
        ag = _get_agent(agent)
        if not ag:
            print(Fore.RED + f"Unknown agent: {agent}", file=sys.stderr)
            raise typer.Exit(1)
        task = ag.full_description
    if not task:
        print(Fore.RED + "Provide a task description or use --agent <name>", file=sys.stderr)
        raise typer.Exit(1)
    asyncio.run(_run_remote(task, backend, yes, api_key, skill))


@app.command()
def review(
    pr_url: str = typer.Argument(..., help="GitHub PR URL"),
    backend: str = typer.Option("http://localhost:8000", help="Nimbus backend URL"),
    post: bool = typer.Option(False, "--post", help="Post the review as a comment on the PR"),
    api_key: Optional[str] = typer.Option(None, help="Nimbus API key"),
):
    """Review a GitHub PR diff."""
    asyncio.run(_review_remote(pr_url, backend, post, api_key))


@app.command()
def issue(
    issue_url: str = typer.Argument(..., help="GitHub issue URL"),
    backend: str = typer.Option("http://localhost:8000", help="Nimbus backend URL"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    token: Optional[str] = typer.Option(None, help="GitHub token"),
    api_key: Optional[str] = typer.Option(None, help="Nimbus API key"),
):
    """Run Nimbus on a GitHub issue."""
    asyncio.run(_issue_remote(issue_url, backend, yes, token, api_key))


@app.command(name="test")
def test_cmd(
    file_path: str = typer.Argument(..., help="Relative path to source file, e.g. services/auth.py"),
    repo_id: Optional[str] = typer.Option(None, "--repo-id", help="Repo ID (auto-detected if omitted)"),
    backend: str = typer.Option("http://localhost:8000", help="Nimbus backend URL"),
    write: bool = typer.Option(False, "--write", help="Write generated tests to disk"),
    api_key: Optional[str] = typer.Option(None, help="Nimbus API key"),
):
    """Generate a test suite for a source file."""
    asyncio.run(_test_remote(file_path, repo_id, backend, write, api_key))


@app.command()
def explain(
    file: str = typer.Argument(..., help="File path, optionally with line range: src/auth.py:42-67"),
):
    """Explain a file or specific line range in plain English."""
    from cli.interactive import NimbusREPL
    repl = NimbusREPL(Path.cwd())
    asyncio.run(repl._explain(file))


@app.command()
def replay(
    speed: float = typer.Option(2.0, help="Playback speed multiplier"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to replay (default: latest)"),
):
    """Replay the last Nimbus session as an animated terminal replay."""
    from cli.local_executor import LocalExecutor
    from cli.renderer import FAINT, GOLD, GREEN, RED, console
    from cli.session_recorder import SessionRecorder

    executor = LocalExecutor(Path.cwd())
    sessions = SessionRecorder.list_sessions(executor.repo_name)
    if not sessions:
        console.print(f"  [{RED}]No sessions found for {executor.repo_name}[/{RED}]")
        raise typer.Exit()

    target = sessions[0] if not session_id else next(
        (s for s in sessions if s["id"] == session_id), sessions[0]
    )
    repo_dir = Path.home() / ".nimbus" / "sessions" / executor.repo_name.replace("/", "_")
    data = json.loads((repo_dir / f"{target['id']}.json").read_text())

    console.print(f"\n  [{GOLD}]◆[/{GOLD}] replaying: {data['task'][:60]}")
    console.print(f"  [{FAINT}]speed: {speed}x  ·  {len(data['events'])} events[/{FAINT}]\n")
    console.print("  Press Ctrl+C to stop\n")
    import time
    time.sleep(0.5)

    prev_ts = data["events"][0]["timestamp"] if data["events"] else time.time()
    for event in data["events"]:
        delay = (event["timestamp"] - prev_ts) / speed
        time.sleep(min(delay, 2.0))
        prev_ts = event["timestamp"]

        etype = event["event_type"]
        d = event.get("data", {})

        if etype == "phase":
            console.print(f"\n  [{GOLD}]◆[/{GOLD}] [white]{d.get('phase', '')}[/white]")
        elif etype == "file_write":
            console.print(f"    [{GOLD}]write[/{GOLD}]   {d.get('path', '')}")
        elif etype == "file_read":
            console.print(f"    [{FAINT}]read    {d.get('path', '')}[/{FAINT}]")
        elif etype == "verify":
            for tool, passed in d.get("results", {}).items():
                icon = f"[{GREEN}]✓[/{GREEN}]" if passed else f"[{RED}]✗[/{RED}]"
                console.print(f"    {icon} {tool}")
        elif etype == "commit":
            console.print(f"  [{GREEN}]◆[/{GREEN}] committed: {d.get('branch', '')}")
        elif etype == "error":
            console.print(f"  [{RED}]✗[/{RED}] {d.get('message', '')}")

    console.print(f"\n  [{GREEN}]replay complete[/{GREEN}]\n")


@app.command()
def watch():
    """Watch the repo and surface AI suggestions as you code."""
    from cli.watcher import start_watch
    start_watch(Path.cwd())


@app.command()
def pair():
    """Real-time pair programming -- suggestions appear as you edit."""
    from cli.pair import start_pair
    start_pair(Path.cwd())


@app.command()
def memory(
    graph: bool = typer.Option(False, "--graph", help="Show interactive memory graph"),
    delete: Optional[str] = typer.Option(None, "--delete", help="Delete a memory entry by ID"),
    repo_path: Optional[str] = typer.Option(None, "--repo", help="Repo path (default: cwd)"),
):
    """View and manage codebase memory for the current repo."""
    import chromadb
    import subprocess as sp
    from rich import box
    from rich.table import Table
    from cli.renderer import FAINT, GOLD, GREEN, RED, console

    CHROMA_DIR = Path.home() / ".nimbus" / "chroma"
    rpath = Path(repo_path) if repo_path else Path.cwd()

    result = sp.run(
        ["git", "-C", str(rpath), "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    repo_name = (
        result.stdout.strip()
        .replace("https://github.com/", "")
        .replace(".git", "")
        .replace("git@github.com:", "")
    )
    collection_name = f"local_{repo_name.replace('/', '_')}"

    try:
        chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = chroma.get_collection(collection_name)
        results = collection.get(include=["documents", "metadatas"])
    except Exception:
        console.print(f"  [{FAINT}]no memory found for {repo_name}[/{FAINT}]")
        return

    docs = results.get("documents", [])
    ids = results.get("ids", [])

    if delete:
        matching = [i for i in ids if i.startswith(delete) or i == delete]
        if matching:
            collection.delete(ids=matching)
            console.print(f"  [{GREEN}]deleted {len(matching)} entr{'y' if len(matching) == 1 else 'ies'}[/{GREEN}]")
        else:
            console.print(f"  [{RED}]entry not found: {delete}[/{RED}]")
        return

    console.print(f"\n  [{GOLD}]codebase memory[/{GOLD}]  ·  {repo_name}")
    console.print(f"  [{FAINT}]{len(docs)} entries[/{FAINT}]\n")

    table = Table(box=box.SIMPLE, show_header=True, header_style=FAINT)
    table.add_column("ID", style=FAINT, width=8)
    table.add_column("Content", style="white", max_width=70)

    for doc_id, doc in zip(ids, docs):
        short_id = doc_id.split(":")[0].split("_")[-1][:6]
        table.add_row(short_id, doc[:120] + ("..." if len(doc) > 120 else ""))

    console.print("  ", table)
    console.print(f"\n  [{FAINT}]use --delete <id> to remove an entry[/{FAINT}]\n")


@skills_app.command("list")
def skills_list(
    backend: str = typer.Option("http://localhost:8000", help="Nimbus backend URL"),
    api_key: Optional[str] = typer.Option(None, help="Nimbus API key"),
):
    """List available skills."""
    async def _go():
        k = api_key or os.environ.get("NIMBUS_API_KEY")
        client = NimbusClient(backend, api_key=k)
        try:
            skills = await client.list_skills()
        except Exception as exc:
            print(Fore.RED + f"Error: {exc}", file=sys.stderr)
            return
        if not skills:
            print("No skills available.")
            return
        for skill in skills:
            tag = Style.DIM + "(built-in)" + Style.RESET_ALL if not skill.get("owner_key_id") else ""
            print(f"  {Fore.CYAN + Style.BRIGHT + skill['name'] + Style.RESET_ALL}  {tag}")
            print(f"    {skill['description']}")
    asyncio.run(_go())


@skills_app.command("create")
def skills_create(
    name: str = typer.Option(..., "--name", help="Skill name"),
    description: str = typer.Option(..., "--description", help="Short description"),
    prompt: str = typer.Option(..., "--prompt", help="System prompt addition"),
    backend: str = typer.Option("http://localhost:8000", help="Nimbus backend URL"),
    api_key: Optional[str] = typer.Option(None, help="Nimbus API key"),
):
    """Create a custom skill."""
    async def _go():
        k = api_key or os.environ.get("NIMBUS_API_KEY")
        client = NimbusClient(backend, api_key=k)
        try:
            skill = await client.create_skill(name, description, prompt)
        except Exception as exc:
            print(Fore.RED + f"Error: {exc}", file=sys.stderr)
            return
        print(Fore.GREEN + f"Created skill: {skill['name']}")
    asyncio.run(_go())


async def _run_remote(task: str, backend: str, yes: bool, api_key: Optional[str], skill: Optional[str]):
    remote_url, repo_slug = get_git_remote()
    repo_name = repo_slug.split("/")[-1] if "/" in repo_slug else repo_slug
    k = api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(backend, api_key=k)

    try:
        workspace = await client.get_or_create_workspace(repo_name)
        print(f"workspace  {workspace['name']}  ({workspace['id'][:8]}...)")
        repo = await client.get_or_create_repo(workspace["id"], remote_url, repo_name)
        print(f"repo       {repo['name']}  ({repo['id'][:8]}...)")
        task_obj = await client.create_task(workspace["id"], repo["id"], task, skill=skill)
        print(f"task       {task_obj['id'][:8]}...  {task_obj['description'][:60]}")
    except Exception as exc:
        print(Fore.RED + f"Error communicating with backend: {exc}", file=sys.stderr)
        return

    if not yes:
        print()
        try:
            answer = input("Start execution? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        if answer != "y":
            print("Aborted.")
            return

    print()
    try:
        async for event in client.stream_task(task_obj["id"]):
            print(_fmt_event(event))
            phase = event.get("phase", "")
            if phase == "awaiting_approval":
                changes = event.get("data", {}).get("changes", [])
                print()
                _print_plan_table(changes)
                print()
                if yes:
                    await client.approve_task(task_obj["id"])
                else:
                    n = len(changes)
                    try:
                        answer = input(f"Proceed with {n} change{'s' if n != 1 else ''}? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\nAborted.")
                        await client.reject_task(task_obj["id"])
                        return
                    if answer == "y":
                        await client.approve_task(task_obj["id"])
                    else:
                        await client.reject_task(task_obj["id"])
                        return
            elif phase == "awaiting_diff_approval":
                diff = event.get("data", {}).get("diff", "")
                print()
                _print_diff(diff)
                print()
                if yes:
                    await client.approve_diff(task_obj["id"])
                else:
                    try:
                        answer = input("Open PR with these changes? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        print("\nAborted.")
                        await client.reject_diff(task_obj["id"])
                        return
                    if answer == "y":
                        await client.approve_diff(task_obj["id"])
                    else:
                        await client.reject_diff(task_obj["id"])
                        return
            elif phase == "done":
                pr_url = event.get("data", {}).get("pr_url")
                print()
                if pr_url:
                    print(Fore.GREEN + Style.BRIGHT + f"PR: {pr_url}")
                else:
                    print(Fore.GREEN + Style.BRIGHT + "Done.")
                return
            elif phase == "failed":
                print()
                print(Fore.RED + Style.BRIGHT + f"Failed: {event.get('message', 'unknown error')}")
                return
    except Exception as exc:
        print(Fore.RED + f"\nConnection error: {exc}", file=sys.stderr)


async def _review_remote(pr_url: str, backend: str, post: bool, api_key: Optional[str]):
    k = api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(backend, api_key=k)
    print(f"Reviewing {pr_url} ...")
    try:
        result = await client.review_pr(pr_url, post=post)
    except Exception as exc:
        print(Fore.RED + f"Error: {exc}", file=sys.stderr)
        return

    review_text: str = result["review"]
    verdict: str = result["verdict"]
    color = _VERDICT_COLOR.get(verdict, Fore.WHITE)

    print()
    for line in review_text.splitlines():
        if "**Verdict**:" in line:
            print(color + Style.BRIGHT + line + Style.RESET_ALL)
        else:
            print(line)
    print()

    if post:
        print(Fore.CYAN + "Review posted to PR.")


async def _issue_remote(issue_url: str, backend: str, yes: bool, token: Optional[str], api_key: Optional[str]):
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", issue_url.rstrip("/"))
    if not match:
        print(Fore.RED + "Invalid GitHub issue URL. Expected: https://github.com/owner/repo/issues/NUMBER", file=sys.stderr)
        return

    owner, repo_name, issue_number_str = match.group(1), match.group(2), match.group(3)
    issue_number = int(issue_number_str)
    repo_full_name = f"{owner}/{repo_name}"
    repo_url = f"https://github.com/{repo_full_name}"

    tok = token or os.environ.get("NIMBUS_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers: dict = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if tok:
        headers["Authorization"] = f"token {tok}"

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}", headers=headers)
            resp.raise_for_status()
            issue_data = resp.json()
    except Exception as exc:
        print(Fore.RED + f"Failed to fetch issue: {exc}", file=sys.stderr)
        return

    title: str = issue_data.get("title", "")
    body: str = issue_data.get("body") or ""
    description = f"{title}\n\n{body}".strip()

    k = api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(backend, api_key=k)

    try:
        workspace = await client.get_or_create_workspace(repo_name)
        print(f"workspace  {workspace['name']}  ({workspace['id'][:8]}...)")
        repo = await client.get_or_create_repo(workspace["id"], repo_url, repo_name)
        print(f"repo       {repo['name']}  ({repo['id'][:8]}...)")
        task_obj = await client.create_task(
            workspace["id"], repo["id"], description,
            issue_number=issue_number, repo_full_name=repo_full_name,
        )
        print(f"task       {task_obj['id'][:8]}...  {task_obj['description'][:60]}")
    except Exception as exc:
        print(Fore.RED + f"Error communicating with backend: {exc}", file=sys.stderr)
        return

    if not yes:
        print()
        try:
            answer = input("Start execution? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        if answer != "y":
            print("Aborted.")
            return

    print()
    try:
        async for event in client.stream_task(task_obj["id"]):
            print(_fmt_event(event))
            phase = event.get("phase", "")
            if phase == "awaiting_approval":
                changes = event.get("data", {}).get("changes", [])
                print()
                _print_plan_table(changes)
                print()
                if yes:
                    await client.approve_task(task_obj["id"])
                else:
                    n = len(changes)
                    try:
                        answer = input(f"Proceed with {n} change{'s' if n != 1 else ''}? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        await client.reject_task(task_obj["id"])
                        return
                    if answer == "y":
                        await client.approve_task(task_obj["id"])
                    else:
                        await client.reject_task(task_obj["id"])
                        return
            elif phase == "awaiting_diff_approval":
                diff = event.get("data", {}).get("diff", "")
                print()
                _print_diff(diff)
                print()
                if yes:
                    await client.approve_diff(task_obj["id"])
                else:
                    try:
                        answer = input("Open PR with these changes? [y/N] ").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        await client.reject_diff(task_obj["id"])
                        return
                    if answer == "y":
                        await client.approve_diff(task_obj["id"])
                    else:
                        await client.reject_diff(task_obj["id"])
                        return
            elif phase == "done":
                pr_url = event.get("data", {}).get("pr_url")
                print()
                if pr_url:
                    print(Fore.GREEN + Style.BRIGHT + f"PR: {pr_url}")
                else:
                    print(Fore.GREEN + Style.BRIGHT + "Done.")
                return
            elif phase == "failed":
                print()
                print(Fore.RED + Style.BRIGHT + f"Failed: {event.get('message', 'unknown error')}")
                return
    except Exception as exc:
        print(Fore.RED + f"\nConnection error: {exc}", file=sys.stderr)


async def _test_remote(file_path: str, repo_id: Optional[str], backend: str, write: bool, api_key: Optional[str]):
    k = api_key or os.environ.get("NIMBUS_API_KEY")
    client = NimbusClient(backend, api_key=k)

    if not repo_id:
        try:
            remote_url, repo_slug = get_git_remote()
            repo_name = repo_slug.split("/")[-1] if "/" in repo_slug else repo_slug
            async with httpx.AsyncClient() as http:
                resp = await http.get(f"{backend}/workspaces/")
                resp.raise_for_status()
                workspaces = resp.json()
            workspace_id = None
            for ws in workspaces:
                if ws["name"] == repo_name:
                    workspace_id = ws["id"]
                    break
            if workspace_id:
                async with httpx.AsyncClient() as http:
                    resp = await http.get(f"{backend}/workspaces/{workspace_id}/repos")
                    resp.raise_for_status()
                    repos = resp.json()
                for repo in repos:
                    if repo["url"] == remote_url:
                        repo_id = repo["id"]
                        break
        except Exception as exc:
            print(Fore.RED + f"Could not auto-detect repo-id: {exc}", file=sys.stderr)
            print(Fore.RED + "Pass --repo-id explicitly.", file=sys.stderr)
            return

    if not repo_id:
        print(Fore.RED + "Could not resolve repo-id. Pass --repo-id explicitly.", file=sys.stderr)
        return

    print(f"Generating tests for {file_path} ...")
    try:
        result = await client.generate_tests_pr(repo_id, file_path)
    except Exception as exc:
        print(Fore.RED + f"Error: {exc}", file=sys.stderr)
        return

    content: str = result["content"]
    test_file_path: str = result["test_file_path"]

    print()
    for line in content.splitlines():
        if re.match(r"^(def test_|async def test_|it\(|test\(|func Test)", line):
            print(Fore.GREEN + Style.BRIGHT + line + Style.RESET_ALL)
        else:
            print(line)
    print()

    if write:
        out_path = Path.cwd() / test_file_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content)
        print(Fore.GREEN + f"Written to {out_path}")
    else:
        print(Style.DIM + f"(use --write to save to {test_file_path})" + Style.RESET_ALL)


def main():
    app()


if __name__ == "__main__":
    main()
