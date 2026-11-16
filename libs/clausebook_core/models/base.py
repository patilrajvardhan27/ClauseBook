# Declarative base and the small columns every table shares.
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Current UTC time, the single clock every timestamp column reads from.
def utcnow() -> datetime:
    return datetime.now(UTC)


# Shared declarative base for every ORM model.
class Base(DeclarativeBase):
    pass


# Mixin adding a UUID primary key.
class UUIDPk:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


# Mixin adding a created_at timestamp.
class TimestampedMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
