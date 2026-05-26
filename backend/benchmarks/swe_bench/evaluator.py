from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def apply_and_evaluate(
    repo_url: str,
    base_commit: str,
    patch: str,
    test_cmd: str,
    instance_id: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"nimbus-eval-{instance_id}-") as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        try:
            subprocess.run(
                ["git", "clone", "--quiet", repo_url, str(repo_dir)],
                check=True, timeout=120, capture_output=True,
            )
            subprocess.run(
                ["git", "checkout", base_commit],
                cwd=str(repo_dir), check=True, capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            return {"instance_id": instance_id, "resolved": False, "error": f"clone/checkout failed: {exc}"}

        patch_file = Path(tmpdir) / "nimbus.patch"
        patch_file.write_text(patch)
        apply = subprocess.run(
            ["git", "apply", "--check", str(patch_file)],
            cwd=str(repo_dir), capture_output=True,
        )
        if apply.returncode != 0:
            return {
                "instance_id": instance_id,
                "resolved": False,
                "error": f"patch does not apply: {apply.stderr.decode()[:500]}",
            }
        subprocess.run(
            ["git", "apply", str(patch_file)],
            cwd=str(repo_dir), check=True, capture_output=True,
        )

        try:
            result = subprocess.run(
                test_cmd, shell=True, cwd=str(repo_dir),
                capture_output=True, timeout=300,
            )
            resolved = result.returncode == 0
            return {
                "instance_id": instance_id,
                "resolved": resolved,
                "test_stdout": result.stdout.decode(errors="replace")[-2000:],
                "test_stderr": result.stderr.decode(errors="replace")[-500:],
                "error": None,
            }
        except subprocess.TimeoutExpired:
            return {"instance_id": instance_id, "resolved": False, "error": "test suite timed out (300s)"}


def evaluate_batch(
    results_path: Path,
    dataset_path: Path | None = None,
) -> list[dict[str, Any]]:
    with open(results_path) as f:
        results = json.load(f)

    try:
        from swebench.harness.run_evaluation import run_instances
        return run_instances(results_path=str(results_path))
    except ImportError:
        pass

    eval_results = []
    for r in results:
        if not r.get("patch"):
            eval_results.append({
                "instance_id": r["instance_id"],
                "resolved": False,
                "error": r.get("error", "no patch generated"),
            })
            continue

        eval_results.append(apply_and_evaluate(
            repo_url=f"https://github.com/{r['repo']}",
            base_commit=r["base_commit"],
            patch=r["patch"],
            test_cmd="python -m pytest tests/ -x -q 2>&1 | tail -20",
            instance_id=r["instance_id"],
        ))

    return eval_results
