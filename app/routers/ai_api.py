"""AI-assisted generation endpoints.

The author provides input at each step (Background, Characters, Outlines,
Chapters, dialog, descriptions, government, etc.) and the AI assists. Context
is assembled from the relevant universe/book data and compressed if it exceeds
the model's context window.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import complete, compress_context, prompt_for
from ..database import get_db
from ..deps import get_current_user
from ..models import Book, Character, Series, Universe

router = APIRouter(prefix="/ai", tags=["ai"])


def _assemble_context(db: Session, universe_id: str | None, book_id: str | None) -> str:
    parts: list[str] = []
    if universe_id:
        u = db.get(Universe, universe_id)
        if u is not None:
            parts.append(f"# Universe: {u.title}\n{u.description}")
            parts.append("## Characters\n" + "\n".join(f"- {c.name}: {c.description}" for c in u.characters))
            parts.append("## Background\n" + "\n".join(f"- {b.title}: {b.body}" for b in u.backgrounds))
            parts.append("## Themes\n" + "\n".join(f"- {t.title}: {t.body}" for t in u.themes))
            parts.append("## Arcs\n" + "\n".join(f"- {a.title}: {a.body}" for a in u.arcs))
    if book_id:
        book = db.get(Book, book_id)
        if book is not None:
            parts.append(f"# Book: {book.title}\n{book.description}")
            parts.append("## Outlines\n" + "\n".join(f"- {o.title}: {o.body}" for o in book.outlines))
            parts.append("## Chapters\n" + "\n".join(f"- {ch.title}: {ch.body}" for ch in book.chapters))
            parts.append("## Book Characters\n" + "\n".join(f"- {c.name}: {c.description}" for c in book.characters))
    context = "\n\n".join(parts)
    return compress_context(context)


@router.post("/generate")
def generate(
    kind: str,
    author_input: str,
    universe_id: str | None = None,
    book_id: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate AI-assisted content for the given ``kind`` (e.g. 'background',
    'character', 'outline', 'chapter', 'dialog', 'government')."""
    context = _assemble_context(db, universe_id, book_id)
    system, user_prompt = prompt_for(kind, author_input, context)
    text = complete(system, user_prompt)
    if not text:
        raise HTTPException(status_code=502, detail="AI generation failed or returned empty")
    return {"kind": kind, "generated": text}
