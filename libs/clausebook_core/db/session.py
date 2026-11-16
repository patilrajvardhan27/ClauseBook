# Database session factory: one engine per process, shared by the API and the worker.
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from clausebook_core.config.settings import Settings


# Opens the engine a session factory is built on.
def build_engine(settings: Settings):
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


# Builds the sessionmaker every request or job pulls a session from.
def build_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = build_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Commits on a clean exit, rolls back otherwise, so callers never manage transactions by hand.
@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
