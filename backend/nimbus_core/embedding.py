from __future__ import annotations

import voyageai
from typing import Sequence

from nimbus_core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self._client: voyageai.AsyncClient | None = None
        self._model = settings.embedding_model

    def _get_client(self) -> voyageai.AsyncClient:
        if self._client is None:
            self._client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
        return self._client

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        client = self._get_client()
        embeddings = []
        batch = settings.embedding_batch_size
        for i in range(0, len(texts), batch):
            chunk = list(texts[i : i + batch])
            result = await client.embed(chunk, model=self._model, input_type="document")
            embeddings.extend(result.embeddings)
        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        client = self._get_client()
        result = await client.embed([text], model=self._model, input_type="query")
        return result.embeddings[0]

    async def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        client = self._get_client()
        result = await client.embed(list(texts), model=self._model, input_type="query")
        return result.embeddings
