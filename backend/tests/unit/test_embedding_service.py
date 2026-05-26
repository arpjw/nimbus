from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nimbus_core.embedding import EmbeddingService


def _make_embed_result(vecs: list[list[float]]) -> MagicMock:
    r = MagicMock()
    r.embeddings = vecs
    return r


@pytest.fixture
def svc():
    with patch("nimbus_core.embedding.voyageai.AsyncClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        service = EmbeddingService()
    service._client = mock_client
    return service, mock_client


def test_get_client_lazy_init():
    svc = EmbeddingService()
    assert svc._client is None
    with patch("nimbus_core.embedding.voyageai.AsyncClient") as mock_cls:
        mock_cls.return_value = MagicMock()
        client = svc._get_client()
    assert client is not None
    assert svc._client is not None


def test_get_client_returns_same_instance():
    svc = EmbeddingService()
    mock_c = MagicMock()
    svc._client = mock_c
    assert svc._get_client() is mock_c


@pytest.mark.asyncio
async def test_embed_query(svc):
    service, mock_client = svc
    mock_client.embed = AsyncMock(return_value=_make_embed_result([[0.1, 0.2, 0.3]]))
    result = await service.embed_query("hello world")
    assert result == [0.1, 0.2, 0.3]
    mock_client.embed.assert_called_once()


@pytest.mark.asyncio
async def test_embed_documents_single_batch(svc):
    service, mock_client = svc
    mock_client.embed = AsyncMock(return_value=_make_embed_result([[0.1], [0.2]]))
    result = await service.embed_documents(["doc a", "doc b"])
    assert len(result) == 2


@pytest.mark.asyncio
async def test_embed_documents_multi_batch(svc):
    service, mock_client = svc
    batch_size = 2
    with patch("nimbus_core.embedding.settings") as mock_settings:
        mock_settings.embedding_batch_size = batch_size
        mock_settings.embedding_model = "voyage-2"
        mock_client.embed = AsyncMock(side_effect=[
            _make_embed_result([[0.1], [0.2]]),
            _make_embed_result([[0.3]]),
        ])
        result = await service.embed_documents(["a", "b", "c"])
    assert len(result) == 3
    assert mock_client.embed.call_count == 2


@pytest.mark.asyncio
async def test_embed_queries(svc):
    service, mock_client = svc
    mock_client.embed = AsyncMock(return_value=_make_embed_result([[0.1], [0.2]]))
    result = await service.embed_queries(["q1", "q2"])
    assert len(result) == 2
