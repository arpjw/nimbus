import threading
import time
from pathlib import Path

import anthropic
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from cli.renderer import FAINT, GOLD, GREEN, console

client = anthropic.Anthropic()


class NimbusWatcher(FileSystemEventHandler):
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.last_check = time.time()
        self.debounce = 30.0
        self.snoozed: set[str] = set()

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if any(skip in path for skip in ["node_modules", ".git", "__pycache__", ".venv"]):
            return
        if not any(path.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js"]):
            return
        if time.time() - self.last_check < self.debounce:
            return
        self.last_check = time.time()
        threading.Thread(target=self._analyze, args=(path,), daemon=True).start()

    def _analyze(self, path: str):
        try:
            content = Path(path).read_text(errors="ignore")[:3000]
            rel_path = Path(path).relative_to(self.repo_path)

            if str(rel_path) in self.snoozed:
                return

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this file for ONE specific, actionable issue worth flagging to a developer.
Only flag if something is genuinely worth addressing: untested functions, potential null refs, missing error handling, obvious security issues.
If nothing is worth flagging, respond with exactly: SKIP

File: {rel_path}
{content}

If flagging, respond with exactly two lines:
LINE1: one-sentence description of the issue (max 80 chars)
LINE2: suggested fix in 5 words or less"""
                }]
            )

            text = response.content[0].text.strip()
            if text == "SKIP" or not text:
                return

            lines = text.split("\n")
            issue = lines[0].replace("LINE1:", "").strip()
            fix = lines[1].replace("LINE2:", "").strip() if len(lines) > 1 else "fix it?"

            console.print(f"\n  [{GOLD}]nimbus[/{GOLD}]  {issue}")
            console.print(f"           {fix}? [{GOLD}]y[/{GOLD}]/[{FAINT}]n[/{FAINT}]/[{FAINT}]s to snooze[/{FAINT}] ", end="")

            try:
                resp = input().strip().lower()
                if resp == "y":
                    console.print(f"  [{FAINT}]task queued -- run `nimbus` to execute[/{FAINT}]")
                elif resp == "s":
                    self.snoozed.add(str(rel_path))
                    console.print(f"  [{FAINT}]snoozed {rel_path}[/{FAINT}]")
            except Exception:
                pass
        except Exception:
            pass


def start_watch(repo_path: Path):
    console.print(f"\n  [{GOLD}]◆[/{GOLD}] nimbus watch  ·  watching {repo_path.name}")
    console.print(f"  [{FAINT}]suggestions appear as you edit -- Ctrl+C to stop[/{FAINT}]\n")

    event_handler = NimbusWatcher(repo_path)
    observer = Observer()
    observer.schedule(event_handler, str(repo_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print(f"\n  [{FAINT}]watcher stopped[/{FAINT}]\n")
    observer.join()
