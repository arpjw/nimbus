import difflib

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

GOLD = "#c4a96a"
GREEN = "#6aab7a"
RED = "#e05c5c"
MUTED = "rgb(160,152,136)"
FAINT = "rgb(80,75,60)"
BG = "#14120c"

ASCII_LOGO = """\
  ███╗   ██╗██╗███╗   ███╗██████╗ ██╗   ██╗███████╗
  ████╗  ██║██║████╗ ████║██╔══██╗██║   ██║██╔════╝
  ██╔██╗ ██║██║██╔████╔██║██████╔╝██║   ██║███████╗
  ██║╚██╗██║██║██║╚██╔╝██║██╔══██╗██║   ██║╚════██║
  ██║ ╚████║██║██║ ╚═╝ ██║██████╔╝╚██████╔╝███████║
  ╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚══════╝"""


def render_welcome(repo_name: str, branch: str, file_count: int, version: str = "1.1.0"):
    logo = Text(ASCII_LOGO, style=f"bold {GOLD}")
    console.print(logo)
    console.print()

    tagline = Text()
    tagline.append("  autonomous software engineering", style=MUTED)
    tagline.append(f"  ·  v{version}", style=FAINT)
    console.print(tagline)
    console.print()

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style=FAINT, width=10)
    grid.add_column(style="white")
    grid.add_row("repo", repo_name)
    grid.add_row("branch", branch)
    grid.add_row("indexed", Text.assemble(
        (f"{file_count} files", "white"),
        ("  ·  ", FAINT),
        ("ready", GREEN)
    ))
    grid.add_row("models", Text.assemble(
        ("opus-4-6", "white"), (" → plan  ", FAINT),
        ("sonnet-4-6", "white"), (" → impl", FAINT)
    ))
    console.print("  ", grid)
    console.print()

    console.rule(style=FAINT)
    console.print()

    hints = Text()
    for cmd, desc in [("help", "commands"), ("status", "repo info"), ("undo", "revert last"), ("quit", "exit")]:
        hints.append(f"  {cmd}", style=GOLD)
        hints.append(f"  {desc}  ", style=FAINT)
    console.print(hints)
    console.print()


def render_plan(plan: dict):
    changes = plan.get("changes", [])
    summary = plan.get("summary", "")
    lines = [f"  {len(changes)} {'file' if len(changes) == 1 else 'files'}"]
    for c in changes:
        action = c.get("action", "modify")
        path = c.get("path", "")
        lines.append(f"  {'├─' if c != changes[-1] else '└─'} {action:<8} {path}")
    if summary:
        lines.append("")
        lines.append(f"  {summary}")
    content = "\n".join(lines)
    console.print(Panel(content, title="[bold]Plan[/bold]", border_style=FAINT, box=box.ROUNDED))


def render_confidence(score: int, chunks: int, ambiguity: str):
    filled = int(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    t = Text()
    t.append(f"\n  confidence  ", style=FAINT)
    t.append(bar, style=GOLD)
    t.append(f"  {score}%\n", style="white")
    t.append(f"  retrieval   {chunks} relevant chunks found\n", style=FAINT)
    t.append(f"  ambiguity   {ambiguity}\n", style=FAINT)
    console.print(t)


def render_phase(phase: str, detail: str = ""):
    icon = "◆"
    console.print(f"\n  [{GOLD}]{icon}[/{GOLD}] [white]{phase}[/white]" + (f"[{FAINT}]  {detail}[/{FAINT}]" if detail else ""))


def render_file_event(action: str, path: str, added: int = 0, removed: int = 0):
    color = GOLD if action == "write" else FAINT
    stat = ""
    if action == "write" and (added or removed):
        stat = f"  [green]+{added}[/green] / [red]-{removed}[/red]"
    console.print(f"    [{color}]{action:<8}[/{color}] {path}{stat}")


def render_diff(old_content: str, new_content: str, path: str):
    diff = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm=""
    ))
    if not diff:
        return
    diff_text = Text()
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            diff_text.append(line + "\n", style=f"bold {GREEN}")
        elif line.startswith("-") and not line.startswith("---"):
            diff_text.append(line + "\n", style=f"bold {RED}")
        elif line.startswith("@@"):
            diff_text.append(line + "\n", style=GOLD)
        else:
            diff_text.append(line + "\n", style=FAINT)
    console.print(Panel(diff_text, title=f"[bold]{path}[/bold]", border_style=FAINT, box=box.ROUNDED))


def render_result(pr_url: str, duration: float, branch: str):
    t = Text()
    t.append(f"\n  ◆ done in {duration:.1f}s\n\n", style=GREEN)
    t.append(f"  branch  {branch}\n", style=FAINT)
    t.append(f"  PR      {pr_url}\n", style=f"underline {GOLD}")
    console.print(t)


def render_error(message: str):
    console.print(f"\n  [{RED}]✗[/{RED}] [white]{message}[/white]\n")


def render_verify(results: dict):
    console.print()
    for tool, passed in results.items():
        icon = f"[{GREEN}]✓[/{GREEN}]" if passed else f"[{RED}]✗[/{RED}]"
        console.print(f"    {icon} {tool}")
    console.print()


def prompt_approval(prompt: str, options: str = "y/n") -> str:
    console.print(f"\n  [{MUTED}]{prompt}[/{MUTED}] [{FAINT}][{options}][/{FAINT}] ", end="")
    return input().strip().lower()
