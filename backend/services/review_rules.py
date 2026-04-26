import uuid
from datetime import datetime, timezone

import anthropic

from config import settings
from services.vector_store import VectorStore

_vector_store = VectorStore()
_anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_EXTRACT_PROMPT = (
    "You are analyzing human code review comments to extract reusable review rules for this repository.\n"
    "Given a PR diff and human reviewer comments, identify patterns that represent repo-specific standards,\n"
    "recurring concerns, or style preferences the team enforces.\n\n"
    "Output a JSON array of rule strings. Each rule should be a concise, actionable statement\n"
    "a reviewer would apply to future PRs (e.g. 'Always add error handling for database calls').\n"
    "Output only the JSON array, no preamble. Return [] if no clear rules can be extracted."
)

_COLLECTION_PREFIX = "review_rules_"


def _collection_name(repo_id: str) -> str:
    return f"{_COLLECTION_PREFIX}{repo_id.replace('-', '_')}"


def _get_collection(repo_id: str):
    return _vector_store._client.get_or_create_collection(
        name=_collection_name(repo_id),
        metadata={"hnsw:space": "cosine"},
    )


class ReviewRulesService:
    async def get_active_rules(self, repo_id: str) -> list[str]:
        try:
            col = _vector_store._client.get_collection(_collection_name(repo_id))
        except Exception:
            return []

        total = col.count()
        if total == 0:
            return []

        results = col.get(
            where={"status": "active"},
            include=["documents"],
        )
        return results.get("documents") or []

    async def add_candidate(self, repo_id: str, rule_text: str) -> str:
        col = _get_collection(repo_id)
        rule_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        col.add(
            ids=[rule_id],
            documents=[rule_text],
            metadatas=[{
                "repo_id": repo_id,
                "signal_count": 0,
                "status": "candidate",
                "created_at": now,
                "last_updated": now,
            }],
        )
        return rule_id

    async def record_signal(self, repo_id: str, rule_id: str, positive: bool) -> None:
        col = _get_collection(repo_id)
        result = col.get(ids=[rule_id], include=["metadatas", "documents"])

        if not result["ids"]:
            return

        meta = result["metadatas"][0]
        doc = result["documents"][0]
        signal_count = meta.get("signal_count", 0) + (1 if positive else -1)

        if signal_count >= 3:
            status = "active"
        elif signal_count <= -2:
            status = "disabled"
        else:
            status = meta.get("status", "candidate")

        col.update(
            ids=[rule_id],
            documents=[doc],
            metadatas=[{
                **meta,
                "signal_count": signal_count,
                "status": status,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }],
        )

    async def extract_candidates(self, repo_id: str, pr_diff: str, human_comments: list[str]) -> list[str]:
        comments_text = "\n".join(f"- {c}" for c in human_comments)
        user_content = (
            f"PR Diff (truncated to 3000 chars):\n{pr_diff[:3000]}\n\n"
            f"Human reviewer comments:\n{comments_text}"
        )

        response = await _anthropic_client.messages.create(
            model=settings.reviewer_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": f"{_EXTRACT_PROMPT}\n\n{user_content}"}],
        )

        import json
        try:
            rules = json.loads(response.content[0].text.strip())
            if isinstance(rules, list):
                return [r for r in rules if isinstance(r, str)]
        except Exception:
            pass
        return []

    async def list_rules(self, repo_id: str) -> list[dict]:
        try:
            col = _vector_store._client.get_collection(_collection_name(repo_id))
        except Exception:
            return []

        total = col.count()
        if total == 0:
            return []

        results = col.get(include=["documents", "metadatas"])

        rules = []
        for rule_id, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
            rules.append({
                "id": rule_id,
                "repo_id": meta.get("repo_id", repo_id),
                "text": doc,
                "signal_count": meta.get("signal_count", 0),
                "status": meta.get("status", "candidate"),
                "created_at": meta.get("created_at", ""),
                "last_updated": meta.get("last_updated", ""),
            })
        return rules

    def store_comment_rules(self, repo_id: str, github_comment_id: int, rule_ids: list[str]) -> None:
        if not rule_ids:
            return
        col = _vector_store._client.get_or_create_collection(
            name=f"comment_rules_{repo_id.replace('-', '_')}",
        )
        col.upsert(
            ids=[str(github_comment_id)],
            documents=[",".join(rule_ids)],
            metadatas=[{"repo_id": repo_id}],
        )

    def get_comment_rules(self, repo_id: str, github_comment_id: int) -> list[str]:
        try:
            col = _vector_store._client.get_collection(
                name=f"comment_rules_{repo_id.replace('-', '_')}",
            )
        except Exception:
            return []
        result = col.get(ids=[str(github_comment_id)], include=["documents"])
        if not result["ids"]:
            return []
        raw = result["documents"][0]
        return [r for r in raw.split(",") if r]

    async def disable_rule(self, repo_id: str, rule_id: str) -> bool:
        col = _get_collection(repo_id)
        result = col.get(ids=[rule_id], include=["metadatas", "documents"])

        if not result["ids"]:
            return False

        meta = result["metadatas"][0]
        doc = result["documents"][0]
        col.update(
            ids=[rule_id],
            documents=[doc],
            metadatas=[{
                **meta,
                "status": "disabled",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }],
        )
        return True
