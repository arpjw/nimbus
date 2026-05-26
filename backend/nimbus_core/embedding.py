from __future__ import annotations

import logging
import voyageai
from typing import Sequence

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from nimbus_core.config import settings

_log = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self._client: voyageai.AsyncClient | None = None
        self._model = settings.embedding_model

    def _get_client(self) -> voyageai.AsyncClient:
        if self._client is None:
            self._client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
        return self._client

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def _embed_with_retry(self, texts: list[str], input_type: str) -> list[list[float]]:
        client = self._get_client()
        result = await client.embed(texts, model=self._model, input_type=input_type)
        return result.embeddings

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        embeddings = []
        batch = settings.embedding_batch_size
        for i in range(0, len(texts), batch):
            chunk = list(texts[i : i + batch])
            embeddings.extend(await self._embed_with_retry(chunk, "document"))
        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        results = await self._embed_with_retry([text], "query")
        return results[0]

    async def embed_queries(self, texts: Sequence[str]) -> list[list[float]]:
        return await self._embed_with_retry(list(texts), "query")
