from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_RESULTS_DIR = Path(__file__).parent / "results"
_DATASET = "princeton-nlp/SWE-bench_Verified"
_PRICE_TABLE: dict[str, dict[str, float]] = {
    "claude-opus-4-7": {"input": 15.0, "output": 75.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
}
_AVG_INPUT_TOKENS_PER_TASK = 80_000
_AVG_OUTPUT_TOKENS_PER_TASK = 8_000


def _estimate_cost(n_tasks: int, planner_model: str, implementer_model: str) -> float:
    def _cost(model: str, inp: int, out: int) -> float:
        p = _PRICE_TABLE.get(model, {"input": 3.0, "output": 15.0})
        return (inp * p["input"] + out * p["output"]) / 1_000_000

    per_task = (
        _cost(planner_model, 10_000, 2_000)
        + _cost(implementer_model, _AVG_INPUT_TOKENS_PER_TASK, _AVG_OUTPUT_TOKENS_PER_TASK)
        + _cost("claude-sonnet-4-6", 30_000, 2_000)
    )
    return per_task * n_tasks


def _load_dataset(limit: int | None = None) -> list[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: pip install datasets swebench")
        sys.exit(1)

    ds = load_dataset(_DATASET, split="test")
    items = list(ds)
    if limit:
        items = items[:limit]
    return items


async def _run_task(item: dict[str, Any], workspace_root: Path, yes: bool) -> dict[str, Any]:
    task_id = item["instance_id"]
    repo_url = f"https://github.com/{item['repo']}"
    base_commit = item["base_commit"]
    problem = item["problem_statement"]

    workspace = workspace_root / task_id
    workspace.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "instance_id": task_id,
        "repo": item["repo"],
        "base_commit": base_commit,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "patch": None,
        "error": None,
        "phase_failed": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "duration_seconds": 0.0,
    }

    t0 = time.monotonic()
    try:
        git_dir = workspace / "repo"
        subprocess.run(["git", "clone", "--quiet", repo_url, str(git_dir)], check=True, timeout=120)
        subprocess.run(["git", "checkout", base_commit], cwd=str(git_dir), check=True, capture_output=True)

        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        os.environ.setdefault("REQUIRE_API_KEY", "false")

        from config import settings
        from models.task import Repo, Workspace, Phase
        from agent.orchestrator import run_task_for_repo

        fake_repo = Repo(id=task_id, url=repo_url, name=item["repo"].split("/")[1])
        patch, token_data = await run_task_for_repo(
            task_description=problem,
            repo=fake_repo,
            workspace_override=git_dir,
            auto_approve=True,
            return_patch=True,
        )
        result["patch"] = patch
        result["input_tokens"] = token_data.get("input_tokens", 0)
        result["output_tokens"] = token_data.get("output_tokens", 0)
        result["cost_usd"] = token_data.get("cost_usd", 0.0)

    except Exception as exc:
        result["error"] = str(exc)
        phase = _classify_error(str(exc))
        result["phase_failed"] = phase

    result["duration_seconds"] = round(time.monotonic() - t0, 1)
    result["finished_at"] = datetime.now(timezone.utc).isoformat()

    try:
        shutil.rmtree(workspace, ignore_errors=True)
    except Exception:
        pass

    return result


def _classify_error(error: str) -> str:
    error_lower = error.lower()
    if "plan" in error_lower or "planning" in error_lower:
        return "planner_failed"
    if "implement" in error_lower:
        return "implementer_failed"
    if "verif" in error_lower or "test" in error_lower:
        return "verifier_failed"
    if "patch" in error_lower or "apply" in error_lower:
        return "patch_failed"
    return "unknown"


async def run(tasks: list[dict[str, Any]], yes: bool, max_concurrent: int = 3) -> list[dict[str, Any]]:
    workspace_root = Path(tempfile.mkdtemp(prefix="nimbus-swebench-"))
    results: list[dict[str, Any]] = []
    sem = asyncio.Semaphore(max_concurrent)

    async def _bounded(item: dict[str, Any]) -> dict[str, Any]:
        async with sem:
            r = await _run_task(item, workspace_root, yes)
            status = "OK" if r["patch"] else f"FAIL({r['phase_failed']})"
            print(f"  {r['instance_id']:50s} {status}  ${r['cost_usd']:.3f}  {r['duration_seconds']}s")
            return r

    coros = [_bounded(item) for item in tasks]
    results = await asyncio.gather(*coros)
    return list(results)


def _save_results(results: list[dict[str, Any]], run_id: str) -> Path:
    _RESULTS_DIR.mkdir(exist_ok=True)
    out = _RESULTS_DIR / f"{run_id}.json"
    out.write_text(json.dumps(results, indent=2))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Nimbus against SWE-bench Verified")
    parser.add_argument("--tasks", default="10", help="Number of tasks to run, or 'all' for full 500")
    parser.add_argument("--confirm-cost", action="store_true", help="Required for runs > 10 tasks")
    parser.add_argument("--yes", action="store_true", help="Auto-approve all plans (required for harness)")
    parser.add_argument("--concurrency", type=int, default=3, help="Max parallel tasks")
    parser.add_argument("--run-id", default=None, help="Custom run identifier")
    args = parser.parse_args()

    n_tasks = None if args.tasks == "all" else int(args.tasks)
    actual_n = 500 if n_tasks is None else n_tasks

    from config import settings
    est = _estimate_cost(actual_n, settings.planner_model, settings.implementer_model)
    print(f"\nSWE-bench Verified harness")
    print(f"  Tasks:          {actual_n}")
    print(f"  Est. cost:      ${est:.2f}")
    print(f"  Planner model:  {settings.planner_model}")
    print(f"  Impl. model:    {settings.implementer_model}")
    print()

    if actual_n > 10 and not args.confirm_cost:
        print("ERROR: runs larger than 10 tasks require --confirm-cost")
        print(f"       Estimated spend: ${est:.2f}")
        print("       Re-run with --confirm-cost to proceed.")
        sys.exit(1)

    if actual_n > 10:
        confirm = input(f"Confirmed: spend up to ${est:.2f} on this run? [yes/N] ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)

    print("Loading dataset...")
    tasks = _load_dataset(limit=n_tasks)
    print(f"Loaded {len(tasks)} tasks\n")

    run_id = args.run_id or f"swebench-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    print(f"Run ID: {run_id}\n")

    results = asyncio.run(run(tasks, yes=True, max_concurrent=args.concurrency))

    out_path = _save_results(results, run_id)
    print(f"\nResults saved: {out_path}")

    from benchmarks.swe_bench.report import print_summary
    print_summary(results)


if __name__ == "__main__":
    main()
