from __future__ import annotations

import pickle
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rank_bm25 import BM25Okapi

from nimbus_core.rag import RAGService, RetrievedChunk, _bm25_cache_path, _rrf


@pytest.fixture
def rag_service():
    emb = MagicMock()
    vs = MagicMock()
    return RAGService(embedding_service=emb, vector_store=vs)


def test_bm25_cache_path_creates_dir(tmp_path: Path):
    with patch("nimbus_core.rag.settings") as mock_s:
        mock_s.bm25_cache_dir = str(tmp_path / "bm25")
        p = _bm25_cache_path("owner/my-repo")
    assert p.parent.exists()
    assert p.name == "owner_my_repo.pkl"


def test_bm25_cache_path_safe_id(tmp_path: Path):
    with patch("nimbus_core.rag.settings") as mock_s:
        mock_s.bm25_cache_dir = str(tmp_path / "bm25")
        p = _bm25_cache_path("a-b/c-d")
    assert "/" not in p.name
    assert "-" not in p.name.replace(".pkl", "")


def test_tokenize_basic(rag_service: RAGService):
    tokens = rag_service._tokenize("Hello, world! This is a test.")
    assert "hello" in tokens
    assert "world" in tokens
    assert "test" in tokens


def test_tokenize_empty(rag_service: RAGService):
    tokens = rag_service._tokenize("")
    assert tokens == []


def test_prime_bm25_stores_in_cache(rag_service: RAGService, tmp_path: Path):
    with patch("nimbus_core.rag._bm25_cache_path", return_value=tmp_path / "test.pkl"):
        rag_service.prime_bm25("repo1", ["doc one", "doc two"], [{}, {}])
    assert "repo1" in rag_service._corpus_cache
    docs, metas, bm25 = rag_service._corpus_cache["repo1"]
    assert len(docs) == 2
    assert isinstance(bm25, BM25Okapi)


def test_build_bm25_persists_to_disk(rag_service: RAGService, tmp_path: Path):
    pkl_path = tmp_path / "corpus.pkl"
    with patch("nimbus_core.rag._bm25_cache_path", return_value=pkl_path):
        rag_service._build_bm25("repo2", ["hello world"], [{"chunk_id": "c1"}])
    assert pkl_path.exists()
    with open(pkl_path, "rb") as f:
        entry = pickle.load(f)
    docs, metas, bm25 = entry
    assert docs == ["hello world"]


def test_load_bm25_from_disk_cache_miss(rag_service: RAGService, tmp_path: Path):
    missing = tmp_path / "nonexistent.pkl"
    with patch("nimbus_core.rag._bm25_cache_path", return_value=missing):
        result = rag_service._load_bm25_from_disk("norepo")
    assert result is None


def test_load_bm25_roundtrip(rag_service: RAGService, tmp_path: Path):
    pkl_path = tmp_path / "round.pkl"
    with patch("nimbus_core.rag._bm25_cache_path", return_value=pkl_path):
        rag_service._build_bm25("repo3", ["foo bar"], [{"chunk_id": "x"}])
        rag_service._corpus_cache.clear()
        result = rag_service._load_bm25_from_disk("repo3")
    assert result is not None
    docs, metas, bm25 = result
    assert docs == ["foo bar"]
    assert "repo3" in rag_service._corpus_cache


def test_load_bm25_corrupt_file(rag_service: RAGService, tmp_path: Path):
    bad = tmp_path / "bad.pkl"
    bad.write_bytes(b"not valid pickle data!!")
    with patch("nimbus_core.rag._bm25_cache_path", return_value=bad):
        result = rag_service._load_bm25_from_disk("repo4")
    assert result is None


@pytest.mark.asyncio
async def test_query_returns_ranked_chunks(rag_service: RAGService, tmp_path: Path):
    rag_service._emb.embed_query = AsyncMock(return_value=[0.1, 0.2])
    rag_service._vs.query_multi_repo = MagicMock(return_value=[
        {"document": "chunk A", "metadata": {"chunk_id": "c1"}},
        {"document": "chunk B", "metadata": {"chunk_id": "c2"}},
    ])

    with patch("nimbus_core.rag.settings") as mock_s:
        mock_s.rag_top_k = 5
        results = await rag_service.query(["repo1"], "search query")

    assert len(results) <= 5
    for r in results:
        assert isinstance(r, RetrievedChunk)
