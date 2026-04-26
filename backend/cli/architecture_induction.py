import json
import anthropic
from pathlib import Path

client = anthropic.AsyncAnthropic()

FACTS_KEY = "_architecture_facts"


async def induce_architecture(repo_path: Path, collection) -> dict:
    candidates = []
    for ext in [".py", ".ts", ".tsx", ".js"]:
        for f in repo_path.rglob(f"*{ext}"):
            if any(skip in str(f) for skip in [".venv", "node_modules", "__pycache__", "test", "spec", "dist", "build", ".git"]):
                continue
            try:
                size = f.stat().st_size
                candidates.append((size, f))
            except Exception:
                continue

    candidates.sort(reverse=True)
    sample_files = [f for _, f in candidates[:15]]

    samples = []
    for fpath in sample_files:
        try:
            content = fpath.read_text(errors="ignore")
            rel = fpath.relative_to(repo_path)
            samples.append(f"=== {rel} ===\n{content[:800]}")
        except Exception:
            continue

    if not samples:
        return {}

    combined = "\n\n".join(samples[:10])

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Analyze these code samples and extract the architectural conventions of this codebase.

Output ONLY valid JSON with these exact keys (use null if not determinable):
{{
  "dominant_style": "functional|oop|mixed",
  "async_pattern": "describe the async approach used",
  "error_handling": "describe the error handling convention",
  "test_framework": "pytest|jest|vitest|mocha|other|none",
  "naming_convention": "snake_case|camelCase|mixed",
  "http_client": "which HTTP client library is used",
  "orm_or_db": "which ORM or DB client is used",
  "validation": "which validation library is used",
  "import_style": "relative|absolute|mixed",
  "key_patterns": ["list", "of", "important", "patterns"],
  "avoid": ["list", "of", "things", "to", "avoid"]
}}

Code samples:
{combined}"""
        }]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1])

    try:
        return json.loads(text)
    except Exception:
        return {}


def facts_to_prompt(facts: dict) -> str:
    if not facts:
        return ""

    lines = ["REPO CONVENTIONS (follow these strictly):"]

    if facts.get("dominant_style"):
        lines.append(f"- Style: {facts['dominant_style']}")
    if facts.get("async_pattern"):
        lines.append(f"- Async: {facts['async_pattern']}")
    if facts.get("error_handling"):
        lines.append(f"- Error handling: {facts['error_handling']}")
    if facts.get("test_framework") and facts["test_framework"] != "none":
        lines.append(f"- Tests: {facts['test_framework']}")
    if facts.get("naming_convention"):
        lines.append(f"- Naming: {facts['naming_convention']}")
    if facts.get("http_client"):
        lines.append(f"- HTTP client: {facts['http_client']}")
    if facts.get("orm_or_db"):
        lines.append(f"- Database: {facts['orm_or_db']}")
    if facts.get("validation"):
        lines.append(f"- Validation: {facts['validation']}")
    if facts.get("key_patterns"):
        for p in facts["key_patterns"][:3]:
            lines.append(f"- Pattern: {p}")
    if facts.get("avoid"):
        for a in facts["avoid"][:3]:
            lines.append(f"- Never use: {a}")

    return "\n".join(lines)
