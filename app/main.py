"""FastAPI application entry point.

Wire up the database, Swagger docs, auth (email/password + Google), the content
hierarchy, authoring elements, AI assistance, artwork and export endpoints.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .first_run import create_first_user, setup_page
from .models import User
from .routers import ai_api, artwork, auth, content, export, items, settings_api

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "An AI-assisted tool for developing books. Organised as "
        "Universe -> Series -> Book, with Characters, Background, Themes, "
        "Arcs, Outlines, Chapters and Ideas (linkable across elements). "
        "All text is markdown; export to TXT, MD, HTML, EPUB and Amazon (KDP)."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def index(request: Request, db: Session = Depends(get_db)):
    """Root: redirect to Swagger docs, or show the first-run setup page."""
    page = setup_page(request, db)
    if page is not None:
        return page
    return RedirectResponse(url="/docs")


@app.post("/setup", include_in_schema=False)
def setup(email: str, password: str, db: Session = Depends(get_db)):
    """First-run setup form handler (creates the initial admin)."""
    if db.scalar(select(User).limit(1)) is not None:
        return RedirectResponse(url="/docs")
    token = create_first_user(email=email, password=password, db=db)
    return JSONResponse({"access_token": token, "token_type": "bearer"})


# Health check (no auth)
@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": settings.app_name}


# Include routers
app.include_router(auth.router)
app.include_router(content.router)
app.include_router(items.router)
app.include_router(ai_api.router)
app.include_router(artwork.router)
app.include_router(export.router)
app.include_router(settings_api.router)
