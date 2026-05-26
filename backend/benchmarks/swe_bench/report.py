from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_report(results: list[dict[str, Any]], eval_results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    total = len(results)
    patched = sum(1 for r in results if r.get("patch"))
    errored = sum(1 for r in results if r.get("error") and not r.get("patch"))

    resolved = 0
    if eval_results:
        resolved = sum(1 for e in eval_results if e.get("resolved"))

    total_cost = sum(r.get("cost_usd", 0.0) for r in results)
    total_input = sum(r.get("input_tokens", 0) for r in results)
    total_output = sum(r.get("output_tokens", 0) for r in results)
    durations = [r.get("duration_seconds", 0.0) for r in results if r.get("duration_seconds")]
    mean_duration = sum(durations) / len(durations) if durations else 0.0

    failure_counts: dict[str, int] = {}
    for r in results:
        if r.get("phase_failed"):
            failure_counts[r["phase_failed"]] = failure_counts.get(r["phase_failed"], 0) + 1

    pass_at_1 = (resolved / total * 100) if total else 0.0
    cost_per_task = total_cost / total if total else 0.0

    return {
        "total_tasks": total,
        "patches_generated": patched,
        "resolved": resolved,
        "failed": errored,
        "pass_at_1_pct": round(pass_at_1, 2),
        "cost_per_task_usd": round(cost_per_task, 4),
        "total_cost_usd": round(total_cost, 4),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "mean_duration_seconds": round(mean_duration, 1),
        "failure_breakdown": failure_counts,
    }


def print_summary(results: list[dict[str, Any]], eval_results: list[dict[str, Any]] | None = None) -> None:
    r = build_report(results, eval_results)
    print("\nSWE-bench Verified -- Nimbus results")
    print("=" * 42)
    print(f"  Total tasks:       {r['total_tasks']}")
    print(f"  Patches generated: {r['patches_generated']}")
    if eval_results:
        print(f"  Resolved (Pass@1): {r['resolved']}  ({r['pass_at_1_pct']:.1f}%)")
    print(f"  Failed/errored:    {r['failed']}")
    print(f"  Total cost:        ${r['total_cost_usd']:.4f}")
    print(f"  Cost per task:     ${r['cost_per_task_usd']:.4f}")
    print(f"  Mean duration:     {r['mean_duration_seconds']}s")
    if r["failure_breakdown"]:
        print("  Failure breakdown:")
        for phase, count in sorted(r["failure_breakdown"].items(), key=lambda x: -x[1]):
            print(f"    {phase}: {count}")
    print()


def save_report(results: list[dict[str, Any]], run_id: str, results_dir: Path, eval_results: list[dict[str, Any]] | None = None) -> Path:
    summary = build_report(results, eval_results)
    out = results_dir / f"{run_id}-report.json"
    out.write_text(json.dumps({"summary": summary, "tasks": results}, indent=2))
    return out
