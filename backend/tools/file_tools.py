import aiofiles
from pathlib import Path
from typing import Optional
import fnmatch

IGNORE_PATTERNS = [
    "*.pyc", "__pycache__", ".git", "node_modules", ".next",
    "dist", "build", ".venv", "venv", "*.min.js", "*.lock",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico",
    "*.woff", "*.woff2", "*.ttf", "*.eot", "*.mp4", "*.mp3",
]

TEXT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt",
    ".yml", ".yaml", ".toml", ".env.example", ".sh", ".bash",
    ".html", ".css", ".scss", ".rs", ".go", ".java", ".rb",
    ".cpp", ".c", ".h", ".cs", ".swift", ".kt", ".sql",
    ".graphql", ".proto", ".dockerfile", "Dockerfile",
}


def _is_ignored(path: Path) -> bool:
    for pat in IGNORE_PATTERNS:
        if fnmatch.fnmatch(path.name, pat):
            return True
    for part in path.parts:
        if part in ("__pycache__", "node_modules", ".git", "dist", "build", ".next"):
            return True
    return False


def _is_text(path: Path) -> bool:
    return path.suffix in TEXT_EXTENSIONS or path.name in TEXT_EXTENSIONS


async def read_file(root: Path, relative_path: str) -> str:
    full = (root / relative_path).resolve()
    if not str(full).startswith(str(root.resolve())):
        raise PermissionError("Path traversal attempt blocked")
    async with aiofiles.open(full, "r", encoding="utf-8", errors="replace") as f:
        return await f.read()


async def write_file(root: Path, relative_path: str, content: str) -> str:
    full = (root / relative_path).resolve()
    if not str(full).startswith(str(root.resolve())):
        raise PermissionError("Path traversal attempt blocked")
    full.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(full, "w", encoding="utf-8") as f:
        await f.write(content)
    return f"Written {relative_path} ({len(content)} chars)"


async def list_files(root: Path, max_files: int = 2000) -> list[dict]:
    results = []
    for path in root.rglob("*"):
        if path.is_file() and not _is_ignored(path) and _is_text(path):
            rel = str(path.relative_to(root))
            results.append({"path": rel, "size": path.stat().st_size, "extension": path.suffix})
            if len(results) >= max_files:
                break
    return results


async def search_in_files(root: Path, pattern: str, file_glob: Optional[str] = None) -> list[dict]:
    matches = []
    import re
    try:
        regex = re.compile(pattern)
    except re.error:
        regex = re.compile(re.escape(pattern))

    for path in root.rglob(file_glob or "*"):
        if path.is_file() and not _is_ignored(path) and _is_text(path):
            try:
                async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = await f.readlines()
                for i, line in enumerate(lines):
                    if regex.search(line):
                        matches.append({
                            "file": str(path.relative_to(root)),
                            "line": i + 1,
                            "content": line.rstrip(),
                        })
            except Exception:
                continue
    return matches[:200]
