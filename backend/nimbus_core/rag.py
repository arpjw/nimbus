from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from nimbus_core.config import settings
from nimbus_core.embedding import EmbeddingService
from nimbus_core.vector_store import VectorStore


@dataclass
class RetrievedChunk:
    document: str
    metadata: dict[str, Any]
    score: float


def _rrf(ranks: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for rank_list in ranks:
        for pos, doc_id in enumerate(rank_list):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + pos + 1)
    return scores


def _bm25_cache_path(repo_id: str) -> Path:
    bm25_dir_str = getattr(settings, "bm25_cache_dir", None)
    if bm25_dir_str:
        bm25_dir = Path(bm25_dir_str)
    else:
        bm25_dir = Path(settings.chroma_persist_dir).parent / "bm25"
    bm25_dir.mkdir(parents=True, exist_ok=True)
    safe_id = repo_id.replace("/", "_").replace("-", "_")
    return bm25_dir / f"{safe_id}.pkl"


class RAGService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore) -> None:
        self._emb = embedding_service
        self._vs = vector_store
        self._corpus_cache: dict[str, tuple[list[str], list[dict], BM25Okapi]] = {}

    def _tokenize(self, text: str) -> list[str]:
        import re
        tokens = re.split(r"[\s\W]+", text.lower())
        return [t for t in tokens if t]

    def _build_bm25(self, repo_id: str, documents: list[str], metadatas: list[dict]) -> BM25Okapi:
        tokenized = [self._tokenize(d) for d in documents]
        bm25 = BM25Okapi(tokenized)
        entry = (documents, metadatas, bm25)
        self._corpus_cache[repo_id] = entry
        try:
            with open(_bm25_cache_path(repo_id), "wb") as fh:
                pickle.dump(entry, fh, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:
            pass
        return bm25

    def _load_bm25_from_disk(self, repo_id: str) -> tuple[list[str], list[dict], BM25Okapi] | None:
        cache_path = _bm25_cache_path(repo_id)
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "rb") as fh:
                entry = pickle.load(fh)
            self._corpus_cache[repo_id] = entry
            return entry
        except Exception:
            return None

    def prime_bm25(self, repo_id: str, documents: list[str], metadatas: list[dict]) -> None:
        self._build_bm25(repo_id, documents, metadatas)

    async def query(
        self,
        repo_ids: list[str],
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        top_k = top_k or settings.rag_top_k
        query_emb = await self._emb.embed_query(query)

        vector_results = self._vs.query_multi_repo(repo_ids, query_emb, n_results=top_k * 2)
        vec_rank = [r["metadata"].get("chunk_id", str(i)) for i, r in enumerate(vector_results)]

        bm25_rank: list[str] = []
        for repo_id in repo_ids:
            if repo_id not in self._corpus_cache:
                self._load_bm25_from_disk(repo_id)
            if repo_id in self._corpus_cache:
                docs, metas, bm25 = self._corpus_cache[repo_id]
                scores = bm25.get_scores(self._tokenize(query))
                indexed = sorted(enumerate(scores), key=lambda x: -x[1])
                for idx, _ in indexed[: top_k * 2]:
                    cid = metas[idx].get("chunk_id", str(idx))
                    if cid not in bm25_rank:
                        bm25_rank.append(cid)

        fused = _rrf([vec_rank, bm25_rank])

        chunk_by_id: dict[str, RetrievedChunk] = {}
        for r in vector_results:
            cid = r["metadata"].get("chunk_id", "")
            chunk_by_id[cid] = RetrievedChunk(
                document=r["document"], metadata=r["metadata"], score=fused.get(cid, 0.0)
            )

        ranked = sorted(chunk_by_id.values(), key=lambda x: -x.score)
        return ranked[:top_k]
