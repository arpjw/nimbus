from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    github_token: str = ""

    planner_model: str = "claude-opus-4-6"
    implementer_model: str = "claude-sonnet-4-6"
    reviewer_model: str = "claude-sonnet-4-6"

    max_implement_iterations: int = 5
    max_implementer_iterations: int = 30
    max_fix_iterations: int = 3

    chroma_persist_dir: str = "./.chroma"
    workspace_base_dir: str = "/tmp/nimbus-workspaces"

    embedding_model: str = "voyage-code-2"
    embedding_batch_size: int = 64
    rag_top_k: int = 20
    rag_bm25_weight: float = 0.3
    rag_vector_weight: float = 0.7

    chunk_max_lines: int = 80
    chunk_overlap_lines: int = 10

    github_webhook_secret: str = ""

    redis_url: str = "redis://localhost:6379/0"
    bm25_cache_dir: str = "./.bm25"

    parallel_threshold: int = 9999
    max_parallel_workers: int = 3
    experimental_parallel: bool = False

    require_api_key: bool = True
    nimbus_open_mode: bool = False
    free_tier_monthly_limit: int = 10
    encryption_key: str = ""
    sandbox_verification: bool = False
    sandbox_image: str = "python:3.12-slim"

    ws_ping_interval: int = 20
    cors_origins: list[str] = [
        "https://get-nimbus.com",
        "https://www.get-nimbus.com",
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    openai_api_key: str = ""

    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_client_id: str = ""
    slack_client_secret: str = ""
    app_base_url: str = "https://api.get-nimbus.com"

    linear_api_key: str = ""
    linear_webhook_secret: str = ""

    @property
    def workspace_path(self) -> Path:
        p = Path(self.workspace_base_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
