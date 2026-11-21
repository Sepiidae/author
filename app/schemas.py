"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TargetType = Literal["character", "outline", "background", "theme", "arc"]

TARGET_TYPES: set[str] = {"character", "outline", "background", "theme", "arc"}


class BaseOut(BaseModel):
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: str | None = None
    is_admin: bool = False


class UserCreate(BaseModel):
    email: str
    password: str


class UserOut(BaseOut):
    id: str
    email: str
    display_name: str | None = None
    is_admin: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
class UniverseCreate(BaseModel):
    title: str
    description: str = ""


class UniverseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class SeriesCreate(BaseModel):
    title: str
    description: str = ""
    order: int = 0


class BookCreate(BaseModel):
    title: str
    description: str = ""
    order: int = 0


class CharacterCreate(BaseModel):
    name: str
    description: str = ""


class TextItemCreate(BaseModel):
    title: str
    body: str = ""


class TextItemUpdate(BaseModel):
    title: str | None = None
    body: str | None = None


class IdeaCreate(BaseModel):
    title: str
    body: str = ""
    targets: list[dict[str, str]] = Field(default_factory=list)


class IdeaTarget(BaseModel):
    target_type: TargetType
    target_id: str


class LinkCreate(BaseModel):
    """Attach/detach an idea to a target."""

    target_type: TargetType
    target_id: str


class ArtworkOut(BaseOut):
    id: str
    book_id: str
    title: str
    filename: str
    content_type: str
    url: str
    created_at: datetime
