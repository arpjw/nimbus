import uuid
from datetime import datetime, timezone

import anthropic

from config import settings
from services.embedding import EmbeddingService
from services.vector_store import VectorStore

_embedding_service = EmbeddingService()
_vector_store = VectorStore()
_anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_EXTRACT_PROMPT = (
    "Given this completed Nimbus task, extract a concise memory entry (max 150 words) "
    "capturing: any coding conventions observed, architectural patterns used, libraries "
    "chosen, and whether the implementation succeeded or failed and why. Output only the "
    "memory text, no preamble."
)


async def write_repo_memory(
    repo_id: str,
    task_description: str,
    plan_raw: str,
    verification_passed: bool,
    error: str | None,
) -> None:
    user_content = (
        f"Task: {task_description}\n\n"
        f"Plan (truncated): {plan_raw[:1000]}\n\n"
        f"Verification passed: {verification_passed}\n"
        f"Error: {error or 'None'}"
    )
    response = await _anthropic_client.messages.create(
        model=settings.implementer_model,
        max_tokens=300,
        messages=[{"role": "user", "content": f"{_EXTRACT_PROMPT}\n\n{user_content}"}],
    )
    memory_text = response.content[0].text.strip()

    embeddings = await _embedding_service.embed_documents([memory_text])

    collection = _vector_store._client.get_or_create_collection(
        name=f"repo_memory_{repo_id}",
        metadata={"hnsw:space": "cosine"},
    )
    collection.upsert(
        ids=[str(uuid.uuid4())],
        embeddings=embeddings,
        documents=[memory_text],
        metadatas=[{
            "repo_id": repo_id,
            "task_description": task_description[:120],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    )


async def list_repo_memory(repo_id: str) -> list[dict]:
    try:
        collection = _vector_store._client.get_collection(name=f"repo_memory_{repo_id}")
    except Exception:
        return []

    total = collection.count()
    if total == 0:
        return []

    results = collection.get(include=["documents", "metadatas"])
    return [
        {"id": entry_id, "text": text, "metadata": meta}
        for entry_id, text, meta in zip(
            results["ids"],
            results["documents"],
            results["metadatas"],
        )
    ]


async def delete_repo_memory(repo_id: str, memory_id: str) -> bool:
    try:
        collection = _vector_store._client.get_collection(name=f"repo_memory_{repo_id}")
    except Exception:
        return False

    result = collection.get(ids=[memory_id], include=["documents"])
    if not result["ids"]:
        return False

    collection.delete(ids=[memory_id])
    return True


async def add_manual_repo_memory(repo_id: str, text: str, label: str) -> dict:
    embeddings = await _embedding_service.embed_documents([text])
    memory_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    collection = _vector_store._client.get_or_create_collection(
        name=f"repo_memory_{repo_id}",
        metadata={"hnsw:space": "cosine"},
    )
    collection.upsert(
        ids=[memory_id],
        embeddings=embeddings,
        documents=[text],
        metadatas=[{
            "repo_id": repo_id,
            "label": label,
            "task_description": label[:120],
            "timestamp": ts,
        }],
    )

    return {
        "id": memory_id,
        "text": text,
        "metadata": {"repo_id": repo_id, "label": label, "timestamp": ts},
    }


async def read_repo_memory(
    repo_id: str,
    query: str,
    top_k: int = 8,
) -> list[dict]:
    try:
        collection = _vector_store._client.get_collection(name=f"repo_memory_{repo_id}")
    except Exception:
        return []

    total = collection.count()
    if total == 0:
        return []

    query_embedding = await _embedding_service.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total),
        include=["documents", "metadatas", "distances"],
    )

    return [
        {"text": text, "metadata": meta, "distance": dist}
        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
