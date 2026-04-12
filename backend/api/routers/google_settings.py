"""
api/routers/google_settings.py

Settings + Google OAuth endpoints:
  GET    /settings             — ดู user preferences
  PUT    /settings             — อัปเดต language / dark mode
  POST   /settings/google/connect    — connect Google account (store token)
  DELETE /settings/google/disconnect — disconnect Google account
  GET    /settings/google/storage    — Drive storage usage
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.models.google_integration import GoogleToken, UserPreference

router = APIRouter()


class UserPreferenceRequest(BaseModel):
    language: Optional[str] = None    # TH | EN
    dark_mode: Optional[bool] = None


class GoogleConnectRequest(BaseModel):
    connected_email: str
    access_token: str
    refresh_token: str
    token_expires_at: str   # ISO datetime string


def _pref_to_dict(p: UserPreference) -> dict:
    return {
        "user_id": str(p.user_id),
        "language": p.language,
        "dark_mode": p.dark_mode,
        "updated_at": str(p.updated_at),
    }


@router.get("/settings")
def get_settings(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดู user preferences ของ current user"""
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = uuid.UUID(str(sub))
    pref = db.query(UserPreference).filter_by(user_id=user_id).first()
    if not pref:
        # Return defaults ถ้ายังไม่มีใน DB
        return {"user_id": str(user_id), "language": "TH", "dark_mode": False}

    return _pref_to_dict(pref)


@router.put("/settings")
def update_settings(
    body: UserPreferenceRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """อัปเดต language / dark mode — persist ข้าม session"""
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = uuid.UUID(str(sub))
    pref = db.query(UserPreference).filter_by(user_id=user_id).first()

    if pref:
        if body.language is not None:
            pref.language = body.language.upper()
        if body.dark_mode is not None:
            pref.dark_mode = body.dark_mode
        pref.updated_at = datetime.utcnow()
    else:
        pref = UserPreference(
            user_id=user_id,
            language=(body.language or "TH").upper(),
            dark_mode=body.dark_mode if body.dark_mode is not None else False,
        )
        db.add(pref)

    db.flush()
    return _pref_to_dict(pref)


@router.post("/settings/google/connect")
def connect_google(
    body: GoogleConnectRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """บันทึก Google OAuth token ของ user"""
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = uuid.UUID(str(sub))
    expires_at = datetime.fromisoformat(body.token_expires_at)

    existing = db.query(GoogleToken).filter_by(user_id=user_id).first()
    if existing:
        existing.connected_email = body.connected_email
        existing.access_token = body.access_token
        existing.refresh_token = body.refresh_token
        existing.token_expires_at = expires_at
        existing.updated_at = datetime.utcnow()
    else:
        db.add(GoogleToken(
            user_id=user_id,
            connected_email=body.connected_email,
            access_token=body.access_token,
            refresh_token=body.refresh_token,
            token_expires_at=expires_at,
        ))

    db.flush()
    return {"message": "Google account connected", "email": body.connected_email}


@router.delete("/settings/google/disconnect")
def disconnect_google(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ลบ Google token — disconnect account"""
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = uuid.UUID(str(sub))
    token = db.query(GoogleToken).filter_by(user_id=user_id).first()
    if token:
        db.delete(token)
        db.flush()

    return {"message": "Google account disconnected"}


@router.get("/settings/google")
def get_google_settings(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดูสถานะ Google connection ของ current user"""
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = uuid.UUID(str(sub))
    token = db.query(GoogleToken).filter_by(user_id=user_id).first()
    if not token:
        return {"connected": False, "email": None}

    return {
        "connected": True,
        "email": token.connected_email,
        "expires_at": str(token.token_expires_at),
    }


@router.get("/settings/google/storage")
def get_google_storage(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    ดู Google Drive storage usage
    ในระบบจริงใช้ Drive API about.get
    ใน test env คืน mock data
    """
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = uuid.UUID(str(sub))
    token = db.query(GoogleToken).filter_by(user_id=user_id).first()
    if not token:
        raise HTTPException(status_code=400, detail="Google account not connected")

    # TODO: ดึงข้อมูลจริงจาก Google Drive API about.get ใน production
    return {
        "used_bytes": 1073741824,    # 1 GB
        "total_bytes": 15728640000,  # 15 GB
        "used_percent": 6.8,
        "warning": False,            # warning เมื่อ > 90%
    }


@router.post("/settings/google/test-connection")
def test_google_connection(
    current_user: dict = Depends(require_pin_verified),
):
    """ทดสอบ Google connection (mock)"""
    return {"status": "connected", "message": "Google connection test successful"}
