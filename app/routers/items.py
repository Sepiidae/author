"""CRUD for the authoring elements: Characters, Background, Themes, Arcs,
Outlines, Chapters, Ideas (with linkable targets).

Every body field is markdown. Ideas can be linked to Characters, Outlines,
Background, Themes and Arcs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    Arc,
    Background,
    Book,
    Character,
    Chapter,
    Idea,
    IdeaTarget,
    Outline,
    Series,
    Theme,
    Universe,
)
from ..schemas import (
    TARGET_TYPES,
    IdeaCreate,
    LinkCreate,
    TextItemCreate,
    TextItemUpdate,
)

router = APIRouter(prefix="/items", tags=["items"])


def _check_universe(db: Session, universe_id: str, user) -> Universe:
    u = db.get(Universe, universe_id)
    if u is None or u.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Universe not found")
    return u


def _check_book(db: Session, book_id: str, user) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    series = db.get(Series, book.series_id)
    universe = db.get(Universe, series.universe_id) if series else None
    if universe is None or universe.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Not authorized")
    return book


# ---------------------------------------------------------------------------
# Characters (universe-level or book-level)
# ---------------------------------------------------------------------------
@router.post("/characters")
def create_character(universe_id: str | None, book_id: str | None, payload: "TextItemCreate", db: Session = Depends(get_db), user=Depends(get_current_user)):
    if book_id:
        _check_book(db, book_id, user)
        obj = Character(name=payload.title, description=payload.body, book_id=book_id)
    else:
        _check_universe(db, universe_id, user)  # type: ignore[arg-type]
        obj = Character(name=payload.title, description=payload.body, universe_id=universe_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/characters/universe/{universe_id}")
def list_universe_characters(universe_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_universe(db, universe_id, user)
    return db.scalars(select(Character).where(Character.universe_id == universe_id)).all()


@router.get("/characters/book/{book_id}")
def list_book_characters(book_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_book(db, book_id, user)
    return db.scalars(select(Character).where(Character.book_id == book_id)).all()


@router.patch("/characters/{character_id}")
def update_character(character_id: str, payload: TextItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Character, character_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Character not found")
    if c.book_id:
        _check_book(db, c.book_id, user)
    else:
        _check_universe(db, c.universe_id, user)  # type: ignore[arg-type]
    if payload.title is not None:
        c.name = payload.title
    if payload.body is not None:
        c.description = payload.body
    db.commit()
    db.refresh(c)
    return c


@router.delete("/characters/{character_id}")
def delete_character(character_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Character, character_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Character not found")
    db.delete(c)
    db.commit()
    return {"deleted": character_id}


# ---------------------------------------------------------------------------
# Background / Themes / Arcs (universe-level markdown items)
# ---------------------------------------------------------------------------
@router.post("/backgrounds")
def create_background(universe_id: str, payload: TextItemCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_universe(db, universe_id, user)
    obj = Background(universe_id=universe_id, title=payload.title, body=payload.body)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/backgrounds/{universe_id}")
def list_backgrounds(universe_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_universe(db, universe_id, user)
    return db.scalars(select(Background).where(Background.universe_id == universe_id)).all()


@router.patch("/backgrounds/{bg_id}")
def update_background(bg_id: str, payload: TextItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bg = db.get(Background, bg_id)
    if bg is None:
        raise HTTPException(status_code=404, detail="Not found")
    _check_universe(db, bg.universe_id, user)
    if payload.title is not None:
        bg.title = payload.title
    if payload.body is not None:
        bg.body = payload.body
    db.commit()
    db.refresh(bg)
    return bg


@router.delete("/backgrounds/{bg_id}")
def delete_background(bg_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bg = db.get(Background, bg_id)
    if bg is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(bg)
    db.commit()
    return {"deleted": bg_id}


@router.post("/themes")
def create_theme(universe_id: str, payload: TextItemCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_universe(db, universe_id, user)
    obj = Theme(universe_id=universe_id, title=payload.title, body=payload.body)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/themes/{universe_id}")
def list_themes(universe_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_universe(db, universe_id, user)
    return db.scalars(select(Theme).where(Theme.universe_id == universe_id)).all()


@router.patch("/themes/{theme_id}")
def update_theme(theme_id: str, payload: TextItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.get(Theme, theme_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Not found")
    _check_universe(db, t.universe_id, user)
    if payload.title is not None:
        t.title = payload.title
    if payload.body is not None:
        t.body = payload.body
    db.commit()
    db.refresh(t)
    return t


@router.delete("/themes/{theme_id}")
def delete_theme(theme_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = db.get(Theme, theme_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(t)
    db.commit()
    return {"deleted": theme_id}


@router.post("/arcs")
def create_arc(universe_id: str, payload: TextItemCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_universe(db, universe_id, user)
    obj = Arc(universe_id=universe_id, title=payload.title, body=payload.body)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/arcs/{universe_id}")
def list_arcs(universe_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_universe(db, universe_id, user)
    return db.scalars(select(Arc).where(Arc.universe_id == universe_id)).all()


@router.patch("/arcs/{arc_id}")
def update_arc(arc_id: str, payload: TextItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.get(Arc, arc_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Not found")
    _check_universe(db, a.universe_id, user)
    if payload.title is not None:
        a.title = payload.title
    if payload.body is not None:
        a.body = payload.body
    db.commit()
    db.refresh(a)
    return a


@router.delete("/arcs/{arc_id}")
def delete_arc(arc_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.get(Arc, arc_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(a)
    db.commit()
    return {"deleted": arc_id}


# ---------------------------------------------------------------------------
# Outlines & Chapters (book-level markdown items)
# ---------------------------------------------------------------------------
@router.post("/outlines")
def create_outline(book_id: str, payload: TextItemCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_book(db, book_id, user)
    obj = Outline(book_id=book_id, title=payload.title, body=payload.body)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/outlines/{book_id}")
def list_outlines(book_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_book(db, book_id, user)
    return db.scalars(select(Outline).where(Outline.book_id == book_id)).all()


@router.patch("/outlines/{outline_id}")
def update_outline(outline_id: str, payload: TextItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = db.get(Outline, outline_id)
    if o is None:
        raise HTTPException(status_code=404, detail="Not found")
    _check_book(db, o.book_id, user)
    if payload.title is not None:
        o.title = payload.title
    if payload.body is not None:
        o.body = payload.body
    db.commit()
    db.refresh(o)
    return o


@router.delete("/outlines/{outline_id}")
def delete_outline(outline_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = db.get(Outline, outline_id)
    if o is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(o)
    db.commit()
    return {"deleted": outline_id}


@router.post("/chapters")
def create_chapter(book_id: str, payload: TextItemCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_book(db, book_id, user)
    obj = Chapter(book_id=book_id, title=payload.title, body=payload.body)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/chapters/{book_id}")
def list_chapters(book_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_book(db, book_id, user)
    return db.scalars(select(Chapter).where(Chapter.book_id == book_id)).all()


@router.get("/chapters-detail/{chapter_id}")
def get_chapter(chapter_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Chapter, chapter_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    return c


@router.patch("/chapters/{chapter_id}")
def update_chapter(chapter_id: str, payload: TextItemUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Chapter, chapter_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    _check_book(db, c.book_id, user)
    if payload.title is not None:
        c.title = payload.title
    if payload.body is not None:
        c.body = payload.body
    db.commit()
    db.refresh(c)
    return c


@router.delete("/chapters/{chapter_id}")
def delete_chapter(chapter_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = db.get(Chapter, chapter_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(c)
    db.commit()
    return {"deleted": chapter_id}


# ---------------------------------------------------------------------------
# Ideas + linkable targets
# ---------------------------------------------------------------------------
@router.post("/ideas")
def create_idea(universe_id: str | None, book_id: str | None, payload: IdeaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    idea = Idea(title=payload.title, body=payload.body)
    if book_id:
        _check_book(db, book_id, user)
        idea.book_id = book_id
    elif universe_id:
        _check_universe(db, universe_id, user)  # type: ignore[arg-type]
        idea.universe_id = universe_id
    for t in payload.targets:
        _validate_target(db, t["target_type"], t["target_id"], user)
        idea.targets.append(IdeaTarget(target_type=t["target_type"], target_id=t["target_id"]))
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def _validate_target(db: Session, target_type: str, target_id: str, user):
    if target_type not in TARGET_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown target type: {target_type}")
    model = {"character": Character, "outline": Outline, "background": Background, "theme": Theme, "arc": Arc}[target_type]
    if db.get(model, target_id) is None:
        raise HTTPException(status_code=404, detail=f"{target_type} not found")


@router.post("/ideas/{idea_id}/links")
def add_idea_link(idea_id: str, payload: LinkCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    idea = db.get(Idea, idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    _validate_target(db, payload.target_type, payload.target_id, user)
    existing = db.scalar(
        select(IdeaTarget).where(
            IdeaTarget.idea_id == idea_id,
            IdeaTarget.target_type == payload.target_type,
            IdeaTarget.target_id == payload.target_id,
        )
    )
    if existing is None:
        db.add(IdeaTarget(idea_id=idea_id, target_type=payload.target_type, target_id=payload.target_id))
        db.commit()
    return {"idea_id": idea_id, "target_type": payload.target_type, "target_id": payload.target_id}


@router.get("/ideas/{idea_id}/links")
def list_idea_links(idea_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.scalars(select(IdeaTarget).where(IdeaTarget.idea_id == idea_id)).all()


@router.delete("/ideas/{idea_id}/links/{target_type}/{target_id}")
def remove_idea_link(idea_id: str, target_type: str, target_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    lt = db.scalar(
        select(IdeaTarget).where(
            IdeaTarget.idea_id == idea_id,
            IdeaTarget.target_type == target_type,
            IdeaTarget.target_id == target_id,
        )
    )
    if lt is None:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(lt)
    db.commit()
    return {"removed": True}


@router.delete("/ideas/{idea_id}")
def delete_idea(idea_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    idea = db.get(Idea, idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    db.delete(idea)
    db.commit()
    return {"deleted": idea_id}
