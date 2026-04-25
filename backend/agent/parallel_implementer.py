import asyncio
import math
from pathlib import Path
from typing import AsyncGenerator

from colorama import Fore, Style

from agent.planner import Plan
from agent.implementer import execute_plan

_WORKER_COLORS = [Fore.CYAN, Fore.YELLOW, Fore.MAGENTA]


async def _collect_worker(
    worker_idx: int,
    sub_plan: Plan,
    workspace: Path,
    results: list[list[str]],
) -> None:
    color = _WORKER_COLORS[worker_idx % len(_WORKER_COLORS)]
    prefix = f"{color}[worker-{worker_idx + 1}]{Style.RESET_ALL}"
    lines: list[str] = []
    async for line in execute_plan(sub_plan, workspace):
        lines.append(f"{prefix} {line}")
    results[worker_idx] = lines


async def execute_plan_parallel(
    plan: Plan,
    workspace: Path,
    max_workers: int = 3,
) -> AsyncGenerator[str, None]:
    changes = plan.changes
    group_size = math.ceil(len(changes) / max_workers)
    groups = [changes[i : i + group_size] for i in range(0, len(changes), group_size)]

    results: list[list[str]] = [[] for _ in groups]

    await asyncio.gather(
        *[
            _collect_worker(idx, Plan(summary=plan.summary, changes=group, raw=plan.raw), workspace, results)
            for idx, group in enumerate(groups)
        ]
    )

    for worker_lines in results:
        for line in worker_lines:
            yield line

    yield "[parallel] All workers complete — merging results"
