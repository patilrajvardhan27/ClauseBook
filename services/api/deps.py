"""FastAPI dependencies: a DB session per request, settings as a singleton."""
from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from clausebook_core.config.settings import Settings, get_settings
from clausebook_core.db.session import build_session_factory
from sqlalchemy.orm import Session


@lru_cache
def _session_factory():
    return build_session_factory(get_settings())


def get_db() -> Generator[Session, None, None]:
    factory = _session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def get_app_settings() -> Settings:
    return get_settings()
