from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _load_toml_config() -> dict:
    config_path = Path.home() / ".nimbus" / "config.toml"
    try:
        import toml
        if config_path.exists():
            return toml.load(config_path)
    except Exception:
        pass
    return {}


class Settings:
    def __init__(self) -> None:
        _cfg = _load_toml_config()

        def _get(key: str, default: str = "") -> str:
            return os.environ.get(key.upper(), str(_cfg.get(key, default)))

        def _get_int(key: str, default: int) -> int:
            try:
                return int(os.environ.get(key.upper(), _cfg.get(key, default)))
            except (ValueError, TypeError):
                return default

        def _get_float(key: str, default: float) -> float:
            try:
                return float(os.environ.get(key.upper(), _cfg.get(key, default)))
            except (ValueError, TypeError):
                return default

        self.anthropic_api_key: str = _get("anthropic_api_key")
        self.voyage_api_key: str = _get("voyage_api_key")
        self.planner_model: str = _get("planner_model", "claude-opus-4-6")
        self.implementer_model: str = _get("implementer_model", "claude-sonnet-4-6")
        self.reviewer_model: str = _get("reviewer_model", "claude-sonnet-4-6")
        self.embedding_model: str = _get("embedding_model", "voyage-code-2")
        self.embedding_batch_size: int = _get_int("embedding_batch_size", 64)
        self.chunk_max_lines: int = _get_int("chunk_max_lines", 80)
        self.chunk_overlap_lines: int = _get_int("chunk_overlap_lines", 10)
        self.chroma_persist_dir: str = _get(
            "chroma_persist_dir",
            str(Path.home() / ".nimbus" / "chroma"),
        )
        self.bm25_cache_dir: str = _get(
            "bm25_cache_dir",
            str(Path.home() / ".nimbus" / "bm25"),
        )
        self.rag_top_k: int = _get_int("rag_top_k", 20)
        self.rag_bm25_weight: float = _get_float("rag_bm25_weight", 0.3)
        self.rag_vector_weight: float = _get_float("rag_vector_weight", 0.7)


settings = Settings()
