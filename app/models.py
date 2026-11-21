"""SQLAlchemy ORM models.

The domain is organised as a hierarchy:

    Universe -> Series -> Book

and each Book (and the Universe / Series) owns Characters, Background, Themes,
Arcs, Outlines, Chapters, Ideas and Artwork. Every piece of prose is stored as
markdown. Ideas can be *linked* to Characters, Outlines, Background, Themes and
Arcs.

Most configuration persists here in the database (see :class:`Setting`), rather
than in YAML.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    tokens: Mapped[list["ApiToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    universes: Mapped[list["Universe"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class ApiToken(Base):
    """A bearer token the user can generate to call the REST API directly."""

    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="token")
    # Only a hash is stored; the raw token is returned once at creation.
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str] = mapped_column(String(12), nullable=False)  # e.g. "ba_1234"
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="tokens")


# ---------------------------------------------------------------------------
# Content hierarchy
# ---------------------------------------------------------------------------
class Universe(Base):
    __tablename__ = "universes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    owner_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")  # markdown
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    owner: Mapped["User"] = relationship(back_populates="universes")
    series: Mapped[list["Series"]] = relationship(
        back_populates="universe", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        back_populates="universe", cascade="all, delete-orphan"
    )
    backgrounds: Mapped[list["Background"]] = relationship(
        back_populates="universe", cascade="all, delete-orphan"
    )
    themes: Mapped[list["Theme"]] = relationship(
        back_populates="universe", cascade="all, delete-orphan"
    )
    arcs: Mapped[list["Arc"]] = relationship(
        back_populates="universe", cascade="all, delete-orphan"
    )
    ideas: Mapped[list["Idea"]] = relationship(
        back_populates="universe", cascade="all, delete-orphan"
    )


class Series(Base):
    __tablename__ = "series"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    universe_id: Mapped[str] = mapped_column(String(32), ForeignKey("universes.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")  # markdown
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    universe: Mapped["Universe"] = relationship(back_populates="series")
    books: Mapped[list["Book"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    series_id: Mapped[str] = mapped_column(String(32), ForeignKey("series.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")  # markdown
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    series: Mapped["Series"] = relationship(back_populates="books")
    outlines: Mapped[list["Outline"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    artwork: Mapped[list["Artwork"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    ideas: Mapped[list["Idea"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")  # markdown
    # A character may belong to the whole universe or be scoped to a book.
    universe_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("universes.id"), nullable=True)
    book_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("books.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    universe: Mapped["Universe"] = relationship(back_populates="characters")
    book: Mapped["Book"] = relationship(back_populates="characters")


class Background(Base):
    """Worldbuilding / setting notes (markdown)."""

    __tablename__ = "backgrounds"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    universe_id: Mapped[str] = mapped_column(String(32), ForeignKey("universes.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")  # markdown
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    universe: Mapped["Universe"] = relationship(back_populates="backgrounds")


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    universe_id: Mapped[str] = mapped_column(String(32), ForeignKey("universes.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")  # markdown
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    universe: Mapped["Universe"] = relationship(back_populates="themes")


class Arc(Base):
    """A story arc (character growth, plot thread) spanning the universe."""

    __tablename__ = "arcs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    universe_id: Mapped[str] = mapped_column(String(32), ForeignKey("universes.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")  # markdown
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    universe: Mapped["Universe"] = relationship(back_populates="arcs")


class Outline(Base):
    """A chapter/scene outline for a book (markdown)."""

    __tablename__ = "outlines"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    book_id: Mapped[str] = mapped_column(String(32), ForeignKey("books.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")  # markdown
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    book: Mapped["Book"] = relationship(back_populates="outlines")


class Chapter(Base):
    """A chapter's prose, stored as markdown."""

    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    book_id: Mapped[str] = mapped_column(String(32), ForeignKey("books.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")  # markdown
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    book: Mapped["Book"] = relationship(back_populates="chapters")


class Idea(Base):
    """A free-form idea that can be linked to many target types."""

    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    universe_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("universes.id"), nullable=True)
    book_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("books.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")  # markdown
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    universe: Mapped["Universe"] = relationship(back_populates="ideas")
    book: Mapped["Book"] = relationship(back_populates="ideas")
    targets: Mapped[list["IdeaTarget"]] = relationship(
        back_populates="idea", cascade="all, delete-orphan"
    )


class IdeaTarget(Base):
    """One link from an :class:`Idea` to a character/outline/background/theme/arc."""

    __tablename__ = "idea_targets"

    idea_id: Mapped[str] = mapped_column(String(32), ForeignKey("ideas.id"), primary_key=True)
    target_type: Mapped[str] = mapped_column(String(20), primary_key=True)  # enum name
    target_id: Mapped[str] = mapped_column(String(32), primary_key=True)

    idea: Mapped["Idea"] = relationship(back_populates="targets")


class Artwork(Base):
    """Artwork attached to a book. Stored as PNG or vector (SVG) on disk."""

    __tablename__ = "artwork"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    book_id: Mapped[str] = mapped_column(String(32), ForeignKey("books.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), default="image/png")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    book: Mapped["Book"] = relationship(back_populates="artwork")


# ---------------------------------------------------------------------------
# Database-persisted configuration
# ---------------------------------------------------------------------------
class Setting(Base):
    """A runtime configuration value persisted in the database."""

    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
