"""CRUD for the content hierarchy: Universe -> Series -> Book."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Book, Series, Universe
from ..schemas import BookCreate, SeriesCreate, UniverseCreate, UniverseUpdate

router = APIRouter(prefix="/content", tags=["content"])


# ---------------------------------------------------------------------------
# Universes
# ---------------------------------------------------------------------------
@router.post("/universes", status_code=201)
def create_universe(payload: UniverseCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    universe = Universe(owner_id=user.id, title=payload.title, description=payload.description)
    db.add(universe)
    db.commit()
    db.refresh(universe)
    return universe


@router.get("/universes")
def list_universes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.scalars(select(Universe).where(Universe.owner_id == user.id)).all()


@router.get("/universes/{universe_id}")
def get_universe(universe_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    u = db.get(Universe, universe_id)
    if u is None or u.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Universe not found")
    return u


@router.patch("/universes/{universe_id}")
def update_universe(universe_id: str, payload: UniverseUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    u = db.get(Universe, universe_id)
    if u is None or u.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Universe not found")
    if payload.title is not None:
        u.title = payload.title
    if payload.description is not None:
        u.description = payload.description
    db.commit()
    db.refresh(u)
    return u


@router.delete("/universes/{universe_id}")
def delete_universe(universe_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    u = db.get(Universe, universe_id)
    if u is None or u.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Universe not found")
    db.delete(u)
    db.commit()
    return {"deleted": universe_id}


# ---------------------------------------------------------------------------
# Series (belongs to a universe)
# ---------------------------------------------------------------------------
@router.post("/series")
def create_series(universe_id: str, payload: SeriesCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    u = db.get(Universe, universe_id)
    if u is None or u.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Universe not found")
    series = Series(universe_id=universe_id, title=payload.title, description=payload.description, order=payload.order)
    db.add(series)
    db.commit()
    db.refresh(series)
    return series


@router.get("/series/{universe_id}")
def list_series(universe_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.scalars(select(Series).where(Series.universe_id == universe_id)).all()


# ---------------------------------------------------------------------------
# Books (belongs to a series)
# ---------------------------------------------------------------------------
@router.post("/books")
def create_book(series_id: str, payload: BookCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    series = db.get(Series, series_id)
    if series is None:
        raise HTTPException(status_code=404, detail="Series not found")
    universe = db.get(Universe, series.universe_id)
    if universe is None or universe.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Not authorized")
    book = Book(series_id=series_id, title=payload.title, description=payload.description, order=payload.order)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.get("/books/{series_id}")
def list_books(series_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.scalars(select(Book).where(Book.series_id == series_id)).all()


@router.get("/books-detail/{book_id}")
def get_book(book_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    series = db.get(Series, book.series_id)
    universe = db.get(Universe, series.universe_id) if series else None
    if universe is None or universe.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Not authorized")
    return book
