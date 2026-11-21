"""Export endpoints for a book."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..export import export_book
from ..models import Book, Series, Universe
from ..routers.items import _check_book

router = APIRouter(prefix="/export", tags=["export"])

FORMATS = ["txt", "md", "html", "amazon", "epub"]


@router.get("/books/{book_id}")
def export(book_id: str, fmt: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Export a book. ``fmt`` is one of: txt, md, html, amazon, epub."""
    book = _check_book(db, book_id, user)
    fmt = fmt.lower()
    if fmt not in FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Choose one of: {', '.join(FORMATS)}")
    try:
        payload, content_type, filename = export_book(book, fmt)
    except Exception as exc:  # pragma: no cover - export errors surfaced to client
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    body = payload.encode("utf-8") if isinstance(payload, str) else payload
    return Response(content=body, media_type=content_type, headers=headers)
