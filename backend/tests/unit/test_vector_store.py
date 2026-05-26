from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nimbus_core.vector_store import VectorStore


@pytest.fixture
def vs():
    with patch("nimbus_core.vector_store.chromadb.PersistentClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        store = VectorStore()
    store._client = mock_client
    return store, mock_client


def test_collection_name_replaces_dashes(vs):
    store, _ = vs
    assert store.collection_name("my-repo-id") == "repo_my_repo_id"


def test_collection_name_no_dashes(vs):
    store, _ = vs
    assert store.collection_name("plain") == "repo_plain"


def test_get_or_create_collection(vs):
    store, mock_client = vs
    mock_col = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col
    result = store.get_or_create_collection("repo1")
    assert result is mock_col
    mock_client.get_or_create_collection.assert_called_once_with(
        name="repo_repo1", metadata={"hnsw:space": "cosine"}
    )


def test_delete_collection_swallows_exception(vs):
    store, mock_client = vs
    mock_client.delete_collection.side_effect = Exception("not found")
    store.delete_collection("repo1")


def test_upsert_delegates_to_collection(vs):
    store, mock_client = vs
    mock_col = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col
    store.upsert("repo1", ["id1"], [[0.1]], ["doc"], [{"k": "v"}])
    mock_col.upsert.assert_called_once()


def test_query_multi_repo_merges_results(vs):
    store, mock_client = vs
    mock_col = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_col
    mock_col.query.return_value = {
        "documents": [["doc1"]],
        "metadatas": [[{"chunk_id": "c1"}]],
        "distances": [[0.1]],
    }
    results = store.query_multi_repo(["repo1", "repo2"], [0.1, 0.2], n_results=5)
    assert len(results) == 2
    assert all("document" in r for r in results)


def test_query_multi_repo_skips_exceptions(vs):
    store, mock_client = vs
    mock_client.get_or_create_collection.side_effect = Exception("no collection")
    results = store.query_multi_repo(["repo1"], [0.1], n_results=5)
    assert results == []
