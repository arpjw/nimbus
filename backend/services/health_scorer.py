import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Optional

import anthropic

client = anthropic.AsyncAnthropic()


def _grade(score: float) -> str:
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "B+"
    if score >= 80: return "B"
    if score >= 75: return "C+"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


def _trend(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None:
        return None
    return round(current - previous, 1)


async def score_test_coverage(repo_path: Path) -> Optional[float]:
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--co", "-q", "--tb=no"],
            cwd=str(repo_path), capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            test_files = list(repo_path.rglob("test_*.py")) + list(repo_path.rglob("*_test.py"))
            src_files = [f for f in repo_path.rglob("*.py") if "test" not in str(f) and ".venv" not in str(f)]
            if src_files:
                ratio = min(len(test_files) / max(len(src_files), 1), 1.0)
                return round(ratio * 100, 1)
    except Exception:
        pass

    try:
        if (repo_path / "package.json").exists():
            result = subprocess.run(
                ["npm", "test", "--", "--coverage", "--passWithNoTests"],
                cwd=str(repo_path), capture_output=True, text=True, timeout=60
            )
            match = re.search(r"All files\s*\|\s*([\d.]+)", result.stdout)
            if match:
                return float(match.group(1))
    except Exception:
        pass

    return None


async def score_tech_debt(repo_path: Path) -> Optional[float]:
    try:
        files = []
        for ext in [".py", ".ts", ".tsx"]:
            files.extend(list(repo_path.rglob(f"*{ext}"))[:4])
        files = [f for f in files if ".venv" not in str(f) and "node_modules" not in str(f)][:10]

        if not files:
            return None

        samples = []
        for f in files[:5]:
            try:
                content = f.read_text(errors="ignore")[:500]
                samples.append(f"=== {f.name} ===\n{content}")
            except Exception:
                continue

        if not samples:
            return None

        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"""Rate this code's technical quality on a scale of 0-100.
Consider: complexity, naming, error handling, code duplication, dead code.
Respond with ONLY a number between 0 and 100.

{chr(10).join(samples[:3])}"""
            }]
        )
        score_text = response.content[0].text.strip()
        score = float(re.search(r'\d+\.?\d*', score_text).group())
        return min(max(score, 0), 100)
    except Exception:
        return None


async def score_doc_coverage(repo_path: Path) -> Optional[float]:
    try:
        py_files = [f for f in repo_path.rglob("*.py") if ".venv" not in str(f)][:50]
        if not py_files:
            return None

        total_functions = 0
        documented_functions = 0

        for f in py_files:
            try:
                content = f.read_text(errors="ignore")
                fns = re.findall(r'^\s*def \w+', content, re.MULTILINE)
                total_functions += len(fns)
                docs = re.findall(r'def \w+[^:]*:\s*"""', content)
                documented_functions += len(docs)
            except Exception:
                continue

        if total_functions == 0:
            return None
        return round((documented_functions / total_functions) * 100, 1)
    except Exception:
        return None


async def score_dep_freshness(repo_path: Path) -> Optional[float]:
    try:
        if (repo_path / "requirements.txt").exists():
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                with open(repo_path / "requirements.txt") as f:
                    total = sum(1 for l in f if l.strip() and not l.startswith("#"))
                if total > 0:
                    fresh = max(0, total - len(outdated))
                    return round((fresh / total) * 100, 1)

        if (repo_path / "package.json").exists():
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                cwd=str(repo_path), capture_output=True, text=True, timeout=30
            )
            outdated_data = {}
            try:
                outdated_data = json.loads(result.stdout) if result.stdout.strip() else {}
            except Exception:
                pass
            with open(repo_path / "package.json") as f:
                pkg = json.load(f)
            total = len(pkg.get("dependencies", {})) + len(pkg.get("devDependencies", {}))
            if total > 0:
                fresh = max(0, total - len(outdated_data))
                return round((fresh / total) * 100, 1)
    except Exception:
        pass
    return None


async def score_security(repo_path: Path) -> Optional[float]:
    score = 100.0
    try:
        issues = 0
        for ext in [".py", ".ts", ".js", ".env.example"]:
            for f in list(repo_path.rglob(f"*{ext}"))[:20]:
                if ".venv" in str(f) or "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(errors="ignore")
                    if re.search(r'(?i)(password|secret|api_key)\s*=\s*["\'][^"\']{8,}["\']', content):
                        issues += 1
                    if re.search(r'f".*SELECT.*{', content) or re.search(r"f'.*SELECT.*{", content):
                        issues += 1
                except Exception:
                    continue

        score = max(50, 100 - (issues * 10))
        return score
    except Exception:
        return None


async def generate_health_snapshot(
    repo_id: str,
    workspace_id: str,
    repo_path: Path,
    previous: Optional[object] = None,
) -> dict:
    results = await asyncio.gather(
        score_test_coverage(repo_path),
        score_tech_debt(repo_path),
        score_doc_coverage(repo_path),
        score_dep_freshness(repo_path),
        score_security(repo_path),
        return_exceptions=True
    )

    test_cov, tech_debt, doc_cov, dep_fresh, security = [
        r if not isinstance(r, Exception) else None for r in results
    ]

    ci_pass = 85.0

    metrics = [m for m in [test_cov, tech_debt, doc_cov, dep_fresh, security, ci_pass] if m is not None]
    overall = round(sum(metrics) / len(metrics), 1) if metrics else None

    snapshot = {
        "repo_id": repo_id,
        "workspace_id": workspace_id,
        "test_coverage": test_cov,
        "tech_debt_score": tech_debt,
        "security_score": security,
        "doc_coverage": doc_cov,
        "dep_freshness": dep_fresh,
        "ci_pass_rate": ci_pass,
        "overall_score": overall,
        "overall_grade": _grade(overall) if overall else None,
    }

    if previous:
        snapshot["test_coverage_delta"] = _trend(test_cov, getattr(previous, "test_coverage", None))
        snapshot["overall_delta"] = _trend(overall, getattr(previous, "overall_score", None))

    return snapshot
