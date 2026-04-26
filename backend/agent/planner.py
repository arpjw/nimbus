"""
Planner: uses RAG context + Claude Opus to produce a structured implementation
plan as a JSON list of FileChange objects.
"""

import json
from dataclasses import dataclass
from typing import Any

import anthropic

from config import settings
from services.rag import RAGService, RetrievedChunk

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


@dataclass
class FileChange:
    path: str
    action: str
    description: str
    rationale: str


@dataclass
class Plan:
    summary: str
    changes: list[FileChange]
    raw: str


PLANNER_SYSTEM = """You are Nimbus Planner — an expert software architect that produces
precise, minimal implementation plans.

Given a task description and relevant code context retrieved via semantic search, output a
JSON object with the following shape:

{
  "summary": "One-sentence summary of the approach",
  "changes": [
    {
      "path": "relative/file/path.py",
      "action": "create | modify | delete",
      "description": "Exact changes to make to this file",
      "rationale": "Why this file needs to change"
    }
  ]
}

Rules:
- Be surgical. Only touch files that must change.
- Use the retrieved context to understand existing patterns, naming, and architecture.
- For new files, describe their full content intention.
- For modifications, describe which functions/classes to touch and how.
- Never include test files in the plan unless the task explicitly asks for tests.
- Output ONLY valid JSON. No markdown, no preamble.
"""


async def generate_plan(
    task_description: str,
    repo_ids: list[str],
    rag_service: RAGService,
    repo_file_tree: str,
    memories: list[dict] | None = None,
    skill_name: str | None = None,
    api_key_id: str | None = None,
) -> Plan:
    system = PLANNER_SYSTEM
    if skill_name and api_key_id:
        from services.skills import SkillsService
        skill = SkillsService().get_skill(skill_name, api_key_id)
        if skill:
            system = skill.system_prompt_addition + "\n\n" + PLANNER_SYSTEM

    chunks: list[RetrievedChunk] = await rag_service.query(repo_ids, task_description, top_k=25)

    context_blocks = []
    for chunk in chunks:
        meta = chunk.metadata
        context_blocks.append(
            f"### {meta.get('file_path', 'unknown')} (lines {meta.get('start_line', '?')}-{meta.get('end_line', '?')})\n"
            f"```{meta.get('language', '')}\n{chunk.document}\n```"
        )

    context = "\n\n".join(context_blocks)

    user_message = f"""## Task
{task_description}

## Repository File Tree
```
{repo_file_tree[:3000]}
```

## Relevant Code Context (retrieved via semantic search)
{context}"""

    if memories:
        bullets = "\n".join(f"- {m['text']}" for m in memories)
        user_message += f"\n\n## Repository Memory (past observations)\n{bullets}"

    user_message += "\n\nProduce the implementation plan JSON now."

    response = await client.messages.create(
        model=settings.planner_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"Planner did not return valid JSON: {raw[:200]}")
        data = json.loads(match.group())

    changes = [FileChange(**c) for c in data.get("changes", [])]
    return Plan(summary=data.get("summary", ""), changes=changes, raw=raw)
