"""First-run bootstrap.

There is **no default password**. On first run, when no user exists yet, the
admin is prompted to provide an email + password in the web UI (the embedded
setup page). This module renders that page and creates the initial admin user.
"""
from __future__ import annotations

from fastapi import Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import create_access_token, hash_password

SETUP_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Book Author — First Run</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f1115; color: #e6e6e6;
         display: flex; min-height: 100vh; align-items: center; justify-content: center; }}
  form {{ background: #1a1d25; padding: 2rem 2.5rem; border-radius: 12px; width: 22rem; }}
  h1 {{ font-size: 1.4rem; }}
  label {{ display: block; margin: 0.75rem 0 0.3rem; font-size: 0.85rem; color: #9aa0aa; }}
  input {{ width: 100%; padding: 0.55rem; border-radius: 6px; border: 1px solid #333;
          background: #0f1115; color: #fff; box-sizing: border-box; }}
  button {{ margin-top: 1.25rem; width: 100%; padding: 0.65rem; border: 0; border-radius: 6px;
           background: #4f6fed; color: #fff; font-size: 1rem; cursor: pointer; }}
  small {{ color: #7a8088; }}
</style></head>
<body>
<form method="post" action="/setup">
  <h1>Book Author — First Run</h1>
  <p><small>No users exist yet. Create the first (admin) account.</small></p>
  <label for="email">Email address</label>
  <input id="email" name="email" type="email" required>
  <label for="password">Password</label>
  <input id="password" name="password" type="password" required minlength="8">
  <button type="submit">Create admin &amp; continue</button>
</form>
</body></html>"""


def setup_page(request: Request, db: Session = Depends(get_db)):
    """Render the first-run setup page if no user exists yet."""
    if db.scalar(select(User).limit(1)) is not None:
        return None  # already set up; caller proceeds normally
    return HTMLResponse(SETUP_HTML)


def create_first_user(email: str, password: str = Form(...), db: Session = Depends(get_db)):
    """Create the initial admin from the setup form, returning an access token."""
    if db.scalar(select(User).limit(1)) is not None:
        raise ValueError("Application already initialised")
    user = User(email=email, password_hash=hash_password(password), is_admin=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(user.id)
