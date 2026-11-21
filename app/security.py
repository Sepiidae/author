"""Password hashing and JWT / bearer-token auth."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Prefix so users can recognise their tokens in the UI (raw token shown once).
TOKEN_PREFIX = "ba_"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(password, hashed)
    except Exception:  # malformed hash
        return False


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def generate_token_pair() -> tuple[str, str]:
    """Return ``(raw_token, prefix)`` for a new API bearer token.

    Only the hash of ``raw_token`` is stored; ``prefix`` is shown to the user so
    they can identify the token later.
    """
    raw = TOKEN_PREFIX + secrets.token_urlsafe(24)
    return raw, raw[:12]


def hash_token(raw: str) -> str:
    return _pwd_context.hash(raw)


def verify_token_hash(raw: str, stored_hash: str) -> bool:
    try:
        return _pwd_context.verify(raw, stored_hash)
    except Exception:
        return False
