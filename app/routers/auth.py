"""Authentication endpoints: register/login, tokens, Google OAuth."""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import ApiToken, User
from ..schemas import Token, UserCreate, UserOut
from ..security import (
    create_access_token,
    generate_token_pair,
    hash_password,
    hash_token,
    verify_password,
)
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _first_user(db: Session) -> User | None:
    return db.scalar(select(User).order_by(User.created_at))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Create the first user as admin; later users are non-admin by default."""
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    is_admin = _first_user(db) is None  # first account becomes the admin
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return Token(access_token=create_access_token(user.id))


@router.post("/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    """Email + password login. Returns a bearer access token."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return user


@router.post("/tokens", status_code=status.HTTP_201_CREATED)
def create_api_token(name: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate an API bearer token the user can use for REST calls.

    The raw token is returned **once**. Only a hash is stored, so it cannot be
    recovered later — generate a new one if lost.
    """
    raw, prefix = generate_token_pair()
    token = ApiToken(
        user_id=user.id,
        name=name or "token",
        token_hash=hash_token(raw),
        prefix=prefix,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return {"name": token.name, "prefix": token.prefix, "token": raw, "created_at": token.created_at}


@router.get("/tokens")
def list_api_tokens(user: User = Depends(get_current_user)):
    """List the user's API tokens (raw secrets are never returned)."""
    return [
        {"id": t.id, "name": t.name, "prefix": t.prefix, "last_used_at": t.last_used_at, "created_at": t.created_at}
        for t in user.tokens
    ]


@router.delete("/tokens/{token_id}")
def revoke_api_token(token_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke (delete) an API token."""
    token = db.get(ApiToken, token_id)
    if token is None or token.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    db.delete(token)
    db.commit()
    return {"revoked": token_id}


# ---------------------------------------------------------------------------
# Google OAuth (optional; disabled unless client id/secret are configured)
# ---------------------------------------------------------------------------
@router.get("/google/login")
async def google_login():
    """Redirect the user to Google's OAuth consent screen."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google login is disabled")
    from urllib.parse import urlencode

    params = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Exchange the Google authorization code and log the user in."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google login is disabled")

    import requests

    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    ).json()
    id_token = token_resp.get("id_token")
    profile = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {token_resp.get('access_token')}"},
        timeout=10,
    ).json()

    user = db.scalar(select(User).where(User.google_sub == profile["sub"]))
    if user is None:
        is_admin = _first_user(db) is None
        user = User(
            email=profile["email"],
            google_sub=profile["sub"],
            display_name=profile.get("name"),
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return Token(access_token=create_access_token(user.id))
