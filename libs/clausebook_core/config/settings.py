# Runtime configuration, read once from the environment.
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


# Every env var a deployment can override; nothing here needs a code change.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLAUSEBOOK_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://clausebook:clausebook@localhost:5432/clausebook"
    opensearch_url: str = "http://localhost:9200"
    opensearch_index_precedent: str = "clausebook-precedent"
    llm_provider: str = "none"  # "none" keeps rules-only mode for local/dev/CI
    llm_model: str = "claude-sonnet-5"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"
    max_llm_concurrency: int = 4


# Builds a fresh Settings instance from the current environment.
def get_settings() -> Settings:
    return Settings()
