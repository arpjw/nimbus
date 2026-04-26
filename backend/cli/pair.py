import select
import sys
import threading
import time
from pathlib import Path

import anthropic
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from cli.renderer import FAINT, GOLD, RED, console

client = anthropic.Anthropic()


class PairHandler(FileSystemEventHandler):
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.last_check: dict[str, float] = {}
        self.suggestion_timeout = 60

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if any(skip in path for skip in ["node_modules", ".git", "__pycache__", ".venv"]):
            return
        if not any(path.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js"]):
            return
        self.last_check[path] = time.time()
        threading.Timer(3.0, self._check_and_analyze, args=(path,)).start()

    def _check_and_analyze(self, path: str):
        if time.time() - self.last_check.get(path, 0) < 2.9:
            return
        try:
            content = Path(path).read_text(errors="ignore")[:3000]
            rel_path = Path(path).relative_to(self.repo_path)

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""You are pair programming. Look at this file for ONE actionable suggestion.
Only suggest something if it's genuinely useful: extract complex function, add null guard, simplify condition, add error handling.
If nothing to suggest, respond: LGTM

File: {rel_path}
{content}

If suggesting, respond with:
ISSUE: one sentence (max 70 chars)
FIX: 5 words max"""
                }]
            )

            text = response.content[0].text.strip()
            if text.startswith("LGTM"):
                return

            lines = text.split("\n")
            issue = next((l.replace("ISSUE:", "").strip() for l in lines if l.startswith("ISSUE:")), "")
            fix = next((l.replace("FIX:", "").strip() for l in lines if l.startswith("FIX:")), "")

            if not issue:
                return

            console.print(f"\n  [{GOLD}]pair[/{GOLD}]  {issue}")
            if fix:
                console.print(f"         {fix}? [{GOLD}]y[/{GOLD}]/[{FAINT}]n[/{FAINT}] ({self.suggestion_timeout}s) ", end="", flush=True)

                rlist, _, _ = select.select([sys.stdin], [], [], self.suggestion_timeout)
                if rlist:
                    resp = sys.stdin.readline().strip().lower()
                    if resp == "y":
                        console.print(f"  [{FAINT}]noted -- mention it in your next nimbus task[/{FAINT}]")
                else:
                    console.print(f"[{FAINT}](expired)[/{FAINT}]")

        except Exception:
            pass


def start_pair(repo_path: Path):
    console.print(f"\n  [{GOLD}]◆[/{GOLD}] nimbus pair  ·  watching {repo_path.name}")
    console.print(f"  [{FAINT}]edit any file -- suggestions appear after each save[/{FAINT}]")
    console.print(f"  [{FAINT}]Ctrl+C to stop[/{FAINT}]\n")

    handler = PairHandler(repo_path)
    observer = Observer()
    observer.schedule(handler, str(repo_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print(f"\n  [{FAINT}]pair session ended[/{FAINT}]\n")
    observer.join()
