"""
Hybrid retrieval: Voyage AI vector search + BM25 keyword search fused via
Reciprocal Rank Fusion (RRF). Supports single-repo and multi-repo queries.
"""

from dataclasses import dataclass
from typing import Any
from rank_bm25 import BM25Okapi
from services.embedding import EmbeddingService
from services.vector_store import VectorStore
from config import settings


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


class RAGService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
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
        self._corpus_cache[repo_id] = (documents, metadatas, bm25)
        return bm25

    def prime_bm25(self, repo_id: str, documents: list[str], metadatas: list[dict]):
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
