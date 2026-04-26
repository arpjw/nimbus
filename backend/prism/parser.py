import json
import anthropic
from collections import defaultdict, deque

client = anthropic.AsyncAnthropic()


async def parse_spec_to_tasks(spec: str) -> list[dict]:
    response = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system="""You are a senior engineer breaking a product spec into discrete implementation tasks for an autonomous coding agent (Nimbus).

Each task must be:
- Scoped to a single concern, achievable in one pull request
- Described with enough precision that an autonomous agent can implement it without ambiguity — include the specific endpoint, file, pattern, or behavior expected
- Assigned a skill only if it clearly applies: add-tests, add-openapi-docs, dependency-audit, add-logging, add-error-handling, or null
- Linked to any task IDs it depends on (tasks that must be merged before this one can begin)
- Ordered so foundational work (schema, models, utilities) comes before dependent work (routes, tests, docs)

Target granularity: each task should take an autonomous agent 10-30 minutes. Not "build auth" (too big). Not "add the import statement" (too small).

Output ONLY valid JSON — no preamble, no explanation, no markdown:
[{"id": 1, "description": "...", "skill": null, "depends_on": [], "priority": 1}]""",
        messages=[{"role": "user", "content": spec}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def topological_sort(tasks: list[dict]) -> list[dict]:
    id_map = {t["id"]: t for t in tasks}
    in_degree = {t["id"]: 0 for t in tasks}
    graph = defaultdict(list)
    for t in tasks:
        for dep in t.get("depends_on", []):
            graph[dep].append(t["id"])
            in_degree[t["id"]] += 1
    queue = deque([t["id"] for t in tasks if in_degree[t["id"]] == 0])
    result = []
    while queue:
        tid = queue.popleft()
        result.append(id_map[tid])
        for neighbor in graph[tid]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return result
