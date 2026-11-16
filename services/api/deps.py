# FastAPI dependencies: a DB session per request, settings as a singleton.
from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from clausebook_core.config.settings import Settings, get_settings
from clausebook_core.db.session import build_session_factory
from sqlalchemy.orm import Session


# Builds the process-wide session factory once.
@lru_cache
def _session_factory():
    return build_session_factory(get_settings())


# Yields a DB session for one request, committing on a clean request and rolling back otherwise.
def get_db() -> Generator[Session, None, None]:
    factory = _session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Returns the current settings.
def get_app_settings() -> Settings:
    return get_settings()
