"""Database engine, session factory and base model.

Supports SQLite (default), PostgreSQL and MariaDB/MySQL. The URL is chosen in
``config.py`` from env / ``.env`` so no password is hard-coded.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


def _engine_kwargs(url: str) -> dict:
    kwargs: dict = {"future": True}
    if url.startswith("sqlite"):
        # Allow use across threads (e.g. uvicorn workers); pysqlite only.
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs.setdefault("pool_pre_ping", True)
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
    return kwargs


engine = create_engine(get_settings().database_url, **_engine_kwargs(get_settings().database_url))

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
