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

    async def _init_executor(self):
        if not hasattr(self.executor, '_indexed') or not self.executor._indexed:
            await self.executor.index()
            self.executor._indexed = True

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

        elif cmd == "chat":
            await self.do_chat()

        elif cmd.startswith("search "):
            query = inp[7:].strip()
            if query:
                await self._do_search(query)

        elif cmd.startswith("run ") and "--tdd" in cmd:
            task_desc = inp[4:].replace("--tdd", "").strip()
            from cli.tdd_executor import run_tdd_task
            chunks, _ = await self.executor.retrieve_context(task_desc, top_k=8)
            await run_tdd_task(task_desc, self.executor.repo_path, chunks, self.executor, None)

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

    async def do_chat(self):
        import anthropic
        from rich.panel import Panel
        from rich import box

        client = anthropic.AsyncAnthropic()
        history = []

        console.print(f"\n  [{GOLD}]nimbus chat[/{GOLD}]  [{FAINT}]ask anything about your codebase · type exit to return[/{FAINT}]\n")

        while True:
            console.print(f"  [{GOLD}]you[/{GOLD}] [{FAINT}]›[/{FAINT}] ", end="")
            try:
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                break

            if user_input.lower() in ("exit", "back", "quit", "q"):
                console.print(f"\n  [{FAINT}]returning to nimbus ›[/{FAINT}]\n")
                break

            if not user_input:
                continue

            context_chunks, chunk_count = await self.executor.retrieve_context(user_input, top_k=10)
            context_text = "\n\n".join(context_chunks[:8])

            history.append({"role": "user", "content": user_input})

            system = f"""You are an expert software engineer answering questions about a specific codebase.

Repo: {self.executor.repo_name}
Branch: {self.executor.branch}

Retrieved codebase context:
{context_text}

Answer accurately and specifically based on the context above.
Always cite the specific file and line range when referencing code: [filename:line_start-line_end]
Be concise but complete. If you don't know something from the context, say so clearly."""

            response = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                messages=history,
            )

            answer = response.content[0].text
            history.append({"role": "assistant", "content": answer})

            console.print()
            console.print(Panel(
                answer,
                border_style=FAINT,
                box=box.ROUNDED,
                padding=(0, 1),
            ))
            console.print()

    async def _do_search(self, query: str):
        from nimbus_core.embedding import EmbeddingService

        try:
            collection = self.executor.chroma.get_collection(self.executor.collection_name)
        except Exception:
            console.print(f"\n  [{FAINT}]codebase not indexed — run nimbus first[/{FAINT}]\n")
            return

        embedder = EmbeddingService()
        embeddings = await embedder.embed_queries([query])

        count = collection.count()
        if count == 0:
            console.print(f"\n  [{FAINT}]no results found[/{FAINT}]\n")
            return

        results = collection.query(
            query_embeddings=embeddings,
            n_results=min(8, count),
            include=["documents", "metadatas", "distances"]
        )

        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        if not docs:
            console.print(f"\n  [{FAINT}]no results found[/{FAINT}]\n")
            return

        console.print(f"\n  [{GOLD}]search[/{GOLD}]  [{FAINT}]{query}[/{FAINT}]  [{FAINT}]{len(docs)} results[/{FAINT}]\n")

        from pathlib import Path as _Path
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            path = meta.get("path", "unknown")
            try:
                rel = str(_Path(path).relative_to(self.executor.repo_path))
            except Exception:
                rel = path
            score = round(1 - dist, 2) if dist else 0
            prefix = "├─" if i < len(docs) - 1 else "└─"
            summary = doc.strip().split("\n")[0][:80] if doc else ""
            console.print(f"  {prefix} [{GOLD}]{rel}[/{GOLD}]  [{FAINT}]score {score}[/{FAINT}]")
            if summary:
                console.print(f"     [{FAINT}]{summary}[/{FAINT}]")
            console.print()

    async def _explain(self, file_path: str):
        import anthropic
        from rich import box
        from rich.panel import Panel

        line_range = None
        path_part = file_path
        if ":" in file_path:
            path_part, range_str = file_path.rsplit(":", 1)
            if "-" in range_str:
                try:
                    start_line, end_line = range_str.split("-")
                    line_range = (int(start_line), int(end_line))
                except ValueError:
                    pass

        full_path = self.executor.repo_path / path_part
        if not full_path.exists():
            render_error(f"File not found: {path_part}")
            return

        content = full_path.read_text(errors="ignore")
        title = path_part
        if line_range:
            lines = content.splitlines()
            content = "\n".join(lines[line_range[0] - 1:line_range[1]])
            title = f"{path_part}:{line_range[0]}-{line_range[1]}"

        client = anthropic.AsyncAnthropic()
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": f"""Explain this code for a senior developer. Be specific, not generic.

Cover:
- Purpose (one sentence)
- Key functions/classes and what they actually do
- Non-obvious patterns or design decisions
- Anything to watch out for (async gotchas, side effects, dependencies)

File: {title}

{content[:4000]}"""}]
        )
        console.print(Panel(response.content[0].text, title=f"[bold]{title}[/bold]", border_style=FAINT, box=box.ROUNDED))
