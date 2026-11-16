"""Runtime configuration, read once from the environment.

Kept in one place so a firm's deployment only ever touches env vars, never
code, to change where Postgres, OpenSearch or the LLM provider live.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


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


def get_settings() -> Settings:
    return Settings()
