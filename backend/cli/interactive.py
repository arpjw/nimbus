import asyncio
import readline
from pathlib import Path

from cli.renderer import FAINT, GOLD, GREEN, console, render_error, render_welcome
from cli.local_executor import LocalExecutor


class NimbusREPL:
    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        self.executor = LocalExecutor(self.repo_path)
        self.history = []
        self.running = True

    def _setup_readline(self):
        readline.set_history_length(500)
        try:
            readline.parse_and_bind("tab: complete")
        except Exception:
            pass

    async def start(self):
        self._setup_readline()
        file_count = self.executor.count_files()
        render_welcome(
            repo_name=self.executor.repo_name,
            branch=self.executor.branch,
            file_count=file_count
        )

        await self.executor.index()

        while self.running:
            try:
                console.print(f"  [{GOLD}]nimbus[/{GOLD}] [{FAINT}]›[/{FAINT}] ", end="")
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                console.print()
                break

            if not user_input:
                continue

            self.history.append(user_input)
            await self.handle(user_input)

    async def handle(self, inp: str):
        cmd = inp.lower().strip()

        if cmd in ("quit", "exit", "q"):
            self.running = False

        elif cmd == "help":
            self._print_help()

        elif cmd == "status":
            self._print_status()

        elif cmd == "undo":
            self.executor.undo()

        elif cmd.startswith("explain "):
            file_path = inp[8:].strip()
            await self._explain(file_path)

        else:
            await self.executor.run_task(inp)

    def _print_help(self):
        from rich.table import Table
        table = Table.grid(padding=(0, 4))
        table.add_column(style=f"bold {GOLD}", width=20)
        table.add_column(style=FAINT)
        cmds = [
            ("status", "show repo and index info"),
            ("undo", "revert last task"),
            ("explain <file>", "explain a file in plain English"),
            ("quit", "exit"),
            ("<anything else>", "run as a task"),
        ]
        for cmd, desc in cmds:
            table.add_row(cmd, desc)
        console.print()
        console.print("  ", table)
        console.print()

    def _print_status(self):
        console.print(f"\n  repo    {self.executor.repo_name}")
        console.print(f"  branch  {self.executor.branch}")
        console.print(f"  path    {self.executor.repo_path}")
        console.print(f"  index   [{GREEN}]ready[/{GREEN}]")
        console.print()

    async def _explain(self, file_path: str):
        import anthropic
        from rich import box
        from rich.panel import Panel
        full_path = self.executor.repo_path / file_path
        if not full_path.exists():
            render_error(f"File not found: {file_path}")
            return
        content = full_path.read_text(errors="ignore")
        client = anthropic.AsyncAnthropic()
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": f"Explain this file concisely for a senior developer. Cover: purpose, key functions, patterns to watch out for.\n\nFile: {file_path}\n\n{content[:4000]}"}]
        )
        console.print(Panel(response.content[0].text, title=f"[bold]{file_path}[/bold]", border_style=FAINT, box=box.ROUNDED))
