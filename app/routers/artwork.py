"""Artwork upload/list/download for a book.

Images are stored as PNG or vector (SVG) on disk under the configured upload
directory; metadata lives in the database.
"""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user
from ..models import Artwork, Book, Series, Universe
from ..routers.items import _check_book

router = APIRouter(prefix="/artwork", tags=["artwork"])

ALLOWED = {
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}


@router.post("/books/{book_id}")
async def upload_artwork(
    book_id: str,
    title: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    book = _check_book(db, book_id, user)
    ext = ALLOWED.get(file.content_type)
    if ext is None:
        raise HTTPException(status_code=400, detail="Only PNG or vector (SVG) images are supported")

    upload_dir = os.path.abspath(get_settings().upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(upload_dir, safe_name)
    contents = await file.read()
    with open(path, "wb") as fh:
        fh.write(contents)

    artwork = Artwork(
        book_id=book_id,
        title=title,
        filename=safe_name,
        content_type=file.content_type,
    )
    db.add(artwork)
    db.commit()
    db.refresh(artwork)
    return {
        "id": artwork.id,
        "book_id": artwork.book_id,
        "title": artwork.title,
        "filename": artwork.filename,
        "content_type": artwork.content_type,
        "url": f"/artwork/{artwork.id}",
        "created_at": artwork.created_at,
    }


@router.get("/books/{book_id}")
def list_artwork(book_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _check_book(db, book_id, user)
    return db.query(Artwork).where(Artwork.book_id == book_id).all()


@router.get("/{artwork_id}")
def download_artwork(artwork_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from fastapi.responses import FileResponse

    artwork = db.get(Artwork, artwork_id)
    if artwork is None:
        raise HTTPException(status_code=404, detail="Artwork not found")
    book = db.get(Book, artwork.book_id)
    series = db.get(Series, book.series_id) if book else None
    universe = db.get(Universe, series.universe_id) if series else None
    if universe is None or universe.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Not authorized")

    path = os.path.join(os.path.abspath(get_settings().upload_dir), artwork.filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(path, media_type=artwork.content_type, filename=artwork.filename)


@router.delete("/{artwork_id}")
def delete_artwork(artwork_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    artwork = db.get(Artwork, artwork_id)
    if artwork is None:
        raise HTTPException(status_code=404, detail="Not found")
    path = os.path.join(os.path.abspath(get_settings().upload_dir), artwork.filename)
    db.delete(artwork)
    db.commit()
    if os.path.exists(path):
        os.remove(path)
    return {"deleted": artwork_id}
