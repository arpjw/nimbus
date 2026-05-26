import difflib
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import anthropic
import chromadb
from rich.text import Text

from cli.renderer import (
    FAINT,
    GOLD,
    GREEN,
    RED,
    console,
    prompt_approval,
    render_confidence,
    render_diff,
    render_error,
    render_file_event,
    render_phase,
    render_plan,
    render_result,
    render_verify,
)
from cli.architecture_induction import induce_architecture, facts_to_prompt, FACTS_KEY
from nimbus_core.chunker import chunk_file
from nimbus_core.embedding import EmbeddingService

CHROMA_DIR = Path.home() / ".nimbus" / "chroma"
SESSIONS_DIR = Path.home() / ".nimbus" / "sessions"

anthropic_client = anthropic.AsyncAnthropic()
_embedder = EmbeddingService()


def _stream_diff_live(old: str, new: str, path: str):
    diff_lines = list(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm=""
    ))
    if not diff_lines:
        return
    text = Text()
    for line in diff_lines[:40]:
        if line.startswith("+") and not line.startswith("+++"):
            text.append(line + "\n", style="bold #6aab7a")
        elif line.startswith("-") and not line.startswith("---"):
            text.append(line + "\n", style="bold #e05c5c")
        elif line.startswith("@@"):
            text.append(line + "\n", style="#c4a96a")
        else:
            text.append(line + "\n", style="rgb(80,75,60)")
    console.print(text)


@dataclass
class LocalTask:
    description: str
    repo_path: Path
    repo_name: str
    branch: str
    skill_prompt: str = ""
    session_log: list = field(default_factory=list)


class LocalExecutor:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.repo_name = self._detect_repo_name()
        self.branch = self._detect_branch()
        self.collection_name = f"local_{self.repo_name.replace('/', '_')}"
        self.chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.last_commit_sha: Optional[str] = None
        self.architecture_facts: dict = {}

    def _detect_repo_name(self) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "remote", "get-url", "origin"],
                capture_output=True, text=True
            )
            url = result.stdout.strip()
            url = url.replace("git@github.com:", "github.com/").replace(".git", "")
            url = url.replace("https://", "").replace("http://", "")
            return url
        except Exception:
            return self.repo_path.name

    def _detect_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "branch", "--show-current"],
                capture_output=True, text=True
            )
            return result.stdout.strip() or "main"
        except Exception:
            return "main"

    def count_files(self) -> int:
        count = 0
        for ext in [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java"]:
            count += len(list(self.repo_path.rglob(f"*{ext}")))
        return count

    async def index(self) -> int:
        render_phase("indexing")
        try:
            collection = self.chroma.get_or_create_collection(self.collection_name)
            count = 0
            for ext in [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"]:
                for fpath in self.repo_path.rglob(f"*{ext}"):
                    if any(skip in str(fpath) for skip in ["node_modules", ".venv", "__pycache__", ".git", "dist", "build"]):
                        continue
                    try:
                        content = fpath.read_text(errors="ignore")
                        chunks = await chunk_file(str(fpath), content, self.collection_name)
                        if chunks:
                            texts = [c["text"] for c in chunks]
                            embeddings = await _embedder.embed_documents(texts)
                            ids = [f"{fpath}:{i}" for i in range(len(chunks))]
                            collection.upsert(ids=ids, embeddings=embeddings, documents=texts,
                                              metadatas=[{"path": str(fpath)} for _ in chunks])
                            count += len(chunks)
                    except Exception:
                        continue
            try:
                existing = collection.get(ids=[FACTS_KEY])
                if existing and existing.get("documents"):
                    self.architecture_facts = json.loads(existing["documents"][0])
                else:
                    self.architecture_facts = await induce_architecture(self.repo_path, collection)
                    if self.architecture_facts:
                        collection.upsert(
                            ids=[FACTS_KEY],
                            documents=[json.dumps(self.architecture_facts)],
                            metadatas=[{"type": "architecture_facts"}],
                            embeddings=[[0.0] * 1024]
                        )
            except Exception:
                pass
            return count
        except Exception as e:
            render_error(f"Indexing failed: {e}")
            return 0

    async def retrieve_context(self, description: str, top_k: int = 15) -> tuple[list[str], int]:
        try:
            collection = self.chroma.get_collection(self.collection_name)
            embeddings = await _embedder.embed_queries([description])
            results = collection.query(query_embeddings=embeddings, n_results=top_k)
            docs = results["documents"][0] if results["documents"] else []
            return docs, len(docs)
        except Exception:
            return [], 0

    async def plan(self, task: LocalTask) -> Optional[dict]:
        render_phase("planning")
        context_chunks, chunk_count = await self.retrieve_context(task.description)

        arch_context = facts_to_prompt(self.architecture_facts)
        system = f"""You are a senior software engineer planning changes to a real codebase.
Repo: {task.repo_name}
{arch_context}
{task.skill_prompt}

Retrieved context:
{chr(10).join(context_chunks[:10])}

Generate a precise implementation plan as JSON:
{{"summary": "...", "changes": [{{"path": "...", "action": "modify|create|delete", "description": "...", "rationale": "..."}}]}}

Output ONLY valid JSON. Be precise and specific."""

        response = await anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": f"Task: {task.description}"}],
            system=system
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        plan = json.loads(raw)

        confidence = min(95, 50 + chunk_count * 3)
        ambiguity = "low" if len(task.description.split()) > 8 else "medium"
        render_plan(plan)
        render_confidence(confidence, chunk_count, ambiguity)

        approval = prompt_approval("Proceed?", "y/n/e to edit")
        if approval == "n":
            return None
        if approval == "e":
            editor = os.environ.get("EDITOR", "nano")
            with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
                json.dump(plan, f, indent=2)
                tmp = f.name
            subprocess.run([editor, tmp])
            with open(tmp) as f:
                plan = json.load(f)
            os.unlink(tmp)
        return plan

    async def implement(self, task: LocalTask, plan: dict) -> dict[str, tuple[str, str]]:
        render_phase("implementing")
        file_snapshots = {}
        context_chunks, _ = await self.retrieve_context(task.description)

        system = f"""You are implementing code changes in a real codebase.
Repo: {task.repo_name}
Context:
{chr(10).join(context_chunks[:8])}

For each file, output ONLY the complete new file content with no explanation.
Start your response with exactly: FILE_CONTENT_START
End with: FILE_CONTENT_END"""

        for change in plan.get("changes", []):
            path = self.repo_path / change["path"]
            action = change.get("action", "modify")

            if action == "delete":
                if path.exists():
                    old = path.read_text(errors="ignore")
                    file_snapshots[change["path"]] = (old, "")
                    path.unlink()
                    render_file_event("delete", change["path"])
                continue

            old_content = ""
            if path.exists():
                old_content = path.read_text(errors="ignore")

            response = await anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": f"Task: {task.description}\n\nFile: {change['path']}\nAction: {change['description']}\n\nCurrent content:\n{old_content[:3000] if old_content else '(new file)'}"
                }],
                system=system
            )
            new_content = response.content[0].text
            if "FILE_CONTENT_START" in new_content:
                new_content = new_content.split("FILE_CONTENT_START")[1]
            if "FILE_CONTENT_END" in new_content:
                new_content = new_content.split("FILE_CONTENT_END")[0]
            new_content = new_content.strip()

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_content)
            file_snapshots[change["path"]] = (old_content, new_content)

            added = new_content.count("\n") - old_content.count("\n") if old_content else new_content.count("\n")
            removed = max(0, -added)
            render_file_event("write", change["path"], max(0, added), max(0, removed))
            _stream_diff_live(old_content, new_content, change["path"])

        return file_snapshots

    async def generate_pr_description(self, task_description: str, snapshots: dict, verify_results: dict) -> str:
        diff_summary = []
        for path, (old, new) in snapshots.items():
            if old != new:
                diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm=""))
                added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
                removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
                diff_summary.append(f"- `{path}` (+{added} -{removed})")

        verify_summary = ", ".join(
            f"{tool} {'✓' if passed else '✗'}" for tool, passed in verify_results.items()
        ) if verify_results else "no verification run"

        response = await anthropic.AsyncAnthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": f"""Write a concise GitHub PR description in Markdown for this change.

Task: {task_description}

Files changed:
{chr(10).join(diff_summary)}

Verification: {verify_summary}

Format:
## What changed
[2-3 sentences describing what was done and why]

## Files changed
[the file list above, each with a one-line description of what changed in that file]

## Testing
[one sentence about verification results]

Keep it factual and specific. No marketing language."""
            }]
        )
        return response.content[0].text.strip()

    def verify(self) -> dict[str, bool]:
        render_phase("verifying")
        results = {}

        if list(self.repo_path.rglob("*.py")):
            if shutil.which("pytest"):
                r = subprocess.run(["python", "-m", "pytest", "--tb=no", "-q"],
                                   capture_output=True, cwd=str(self.repo_path))
                results["pytest"] = r.returncode == 0
            elif shutil.which("python"):
                r = subprocess.run(["python", "-m", "py_compile"] +
                                   [str(f) for f in self.repo_path.rglob("*.py")][:20],
                                   capture_output=True, cwd=str(self.repo_path))
                results["py_compile"] = r.returncode == 0

        if list(self.repo_path.rglob("tsconfig.json")):
            if shutil.which("tsc"):
                r = subprocess.run(["tsc", "--noEmit"],
                                   capture_output=True, cwd=str(self.repo_path))
                results["tsc"] = r.returncode == 0
            elif shutil.which("npx"):
                r = subprocess.run(["npx", "tsc", "--noEmit"],
                                   capture_output=True, cwd=str(self.repo_path))
                results["tsc"] = r.returncode == 0

        if list(self.repo_path.rglob("*.go")):
            if shutil.which("go"):
                r = subprocess.run(["go", "build", "./..."],
                                   capture_output=True, cwd=str(self.repo_path))
                results["go build"] = r.returncode == 0

        if list(self.repo_path.rglob("Cargo.toml")):
            if shutil.which("cargo"):
                r = subprocess.run(["cargo", "check"],
                                   capture_output=True, cwd=str(self.repo_path))
                results["cargo"] = r.returncode == 0

        render_verify(results)
        return results

    def show_diff(self, snapshots: dict[str, tuple[str, str]]):
        for path, (old, new) in snapshots.items():
            if old != new:
                render_diff(old, new, path)

    def commit(self, description: str, plan: dict) -> Optional[str]:
        branch = f"nimbus/{description[:40].lower().replace(' ', '-').replace('/', '-')}"
        try:
            subprocess.run(["git", "-C", str(self.repo_path), "checkout", "-b", branch], capture_output=True)
            subprocess.run(["git", "-C", str(self.repo_path), "add", "-A"], capture_output=True)
            msg = f"[Nimbus] {description[:72]}"
            subprocess.run(["git", "-C", str(self.repo_path), "commit", "-m", msg], capture_output=True)
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "rev-parse", "HEAD"],
                capture_output=True, text=True
            )
            self.last_commit_sha = result.stdout.strip()
            return branch
        except Exception as e:
            render_error(f"Commit failed: {e}")
            return None

    def undo(self) -> bool:
        try:
            if self.last_commit_sha:
                subprocess.run(["git", "-C", str(self.repo_path), "reset", "--hard", "HEAD~1"], capture_output=True)
                subprocess.run(["git", "-C", str(self.repo_path), "checkout", self.branch], capture_output=True)
                self.last_commit_sha = None
                console.print(f"  [{GOLD}]◆[/{GOLD}] [white]reverted last task[/white]")
                return True
            return False
        except Exception:
            return False

    async def run_task(self, description: str, skill_prompt: str = "") -> bool:
        from cli.config import load_config
        from cli import sounds as sfx
        from cli.session_recorder import SessionRecorder

        start = time.time()
        config = load_config()
        sound_on = config.get("local", {}).get("sound", False)
        recorder = SessionRecorder(self.repo_name, description)

        if sound_on:
            sfx.play_start()

        task = LocalTask(
            description=description,
            repo_path=self.repo_path,
            repo_name=self.repo_name,
            branch=self.branch,
            skill_prompt=skill_prompt
        )

        recorder.record("phase", {"phase": "planning"})
        plan = await self.plan(task)
        if not plan:
            recorder.record("error", {"message": "planning cancelled"})
            recorder.save()
            return False

        recorder.record("phase", {"phase": "implementing"})
        for change in plan.get("changes", []):
            recorder.record("file_write", {"path": change.get("path", "")})

        snapshots = await self.implement(task, plan)

        recorder.record("phase", {"phase": "verifying"})
        verify_results = self.verify()

        all_passed = all(verify_results.values()) if verify_results else True
        if sound_on and all_passed:
            sfx.play_success()

        recorder.record("verify", {"results": verify_results})

        pr_description = await self.generate_pr_description(description, snapshots, verify_results)

        from rich import box
        from rich.panel import Panel
        console.print(Panel(pr_description, title="[bold]PR description[/bold]", border_style=FAINT, box=box.ROUNDED))

        approval = prompt_approval("Commit?", "y/n/d to view diff")
        if approval == "d":
            self.show_diff(snapshots)
            approval = prompt_approval("Commit?", "y/n")

        if approval != "y":
            for path, (old, _) in snapshots.items():
                fpath = self.repo_path / path
                if old:
                    fpath.write_text(old)
                elif fpath.exists():
                    fpath.unlink()
            console.print(f"  [{FAINT}]changes discarded[/{FAINT}]")
            recorder.record("error", {"message": "changes discarded by user"})
            recorder.save()
            return False

        branch = self.commit(description, plan)
        if not branch:
            if sound_on:
                sfx.play_failed()
            recorder.record("error", {"message": "commit failed"})
            recorder.save()
            return False

        recorder.record("commit", {"branch": branch})

        push = prompt_approval("Push and open PR?", "y/n")
        pr_url = None
        if push == "y":
            subprocess.run(["git", "-C", str(self.repo_path), "push", "-u", "origin", branch], capture_output=True)
            pr_url = f"https://github.com/{self.repo_name}/compare/{branch}"
            if sound_on:
                sfx.play_complete()

        if sound_on and push != "y":
            sfx.play_complete()

        recorder.save(pr_url)

        duration = time.time() - start
        render_result(pr_url or f"branch: {branch}", duration, branch)
        return True
