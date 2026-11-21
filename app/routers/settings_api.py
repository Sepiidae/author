"""Database-persisted configuration.

Most runtime configuration lives in the database (see :class:`app.models.Setting`),
rather than in YAML. Only *basic* settings are in ``config.yaml``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Setting

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def list_settings(db: Session = Depends(get_db)):
    return {s.key: s.value for s in db.scalars(select(Setting)).all()}


@router.get("/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    s = db.scalar(select(Setting).where(Setting.key == key))
    if s is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": s.key, "value": s.value}


@router.put("/{key}")
def set_setting(key: str, value: str, db: Session = Depends(get_db), user=Depends(require_admin)):
    s = db.scalar(select(Setting).where(Setting.key == key))
    if s is None:
        s = Setting(key=key, value=value)
        db.add(s)
    else:
        s.value = value
    db.commit()
    return {"key": s.key, "value": s.value}


@router.delete("/{key}")
def delete_setting(key: str, db: Session = Depends(get_db), user=Depends(require_admin)):
    s = db.scalar(select(Setting).where(Setting.key == key))
    if s is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(s)
    db.commit()
    return {"deleted": key}
