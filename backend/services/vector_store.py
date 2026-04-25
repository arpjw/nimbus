import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Any
from config import settings


class VectorStore:
    def __init__(self):
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def collection_name(self, repo_id: str) -> str:
        return f"repo_{repo_id.replace('-', '_')}"

    def get_or_create_collection(self, repo_id: str):
        return self._client.get_or_create_collection(
            name=self.collection_name(repo_id),
            metadata={"hnsw:space": "cosine"},
        )

    def delete_collection(self, repo_id: str):
        try:
            self._client.delete_collection(self.collection_name(repo_id))
        except Exception:
            pass

    def upsert(self, repo_id: str, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict[str, Any]]):
        col = self.get_or_create_collection(repo_id)
        col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, repo_id: str, query_embedding: list[float], n_results: int = 20) -> dict:
        col = self.get_or_create_collection(repo_id)
        return col.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    def query_multi_repo(self, repo_ids: list[str], query_embedding: list[float], n_results: int = 20) -> list[dict]:
        all_results = []
        for repo_id in repo_ids:
            try:
                r = self.query(repo_id, query_embedding, n_results)
                for doc, meta, dist in zip(
                    r["documents"][0], r["metadatas"][0], r["distances"][0]
                ):
                    all_results.append({"document": doc, "metadata": meta, "distance": dist})
            except Exception:
                continue
        all_results.sort(key=lambda x: x["distance"])
        return all_results[:n_results]
