"""Database session factory.

One engine per process. The worker and the API each build their own session
from the same settings object, so connection pooling never crosses a process
boundary by accident.
"""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from clausebook_core.config.settings import Settings


def build_engine(settings: Settings):
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


def build_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = build_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Commits on a clean exit, rolls back otherwise. Callers never manage transactions by hand."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
