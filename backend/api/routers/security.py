"""api/routers/security.py — Security feature endpoints"""
import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.models.user import User, PinAttempt

router = APIRouter()


@router.get("/security/account-status/{user_id}")
def get_account_security_status(
    user_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": str(user.id),
        "pin_locked": user.pin_locked,
        "is_active": user.is_active,
    }


@router.post("/security/unlock/{user_id}")
def unlock_account(
    user_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pin_locked = False
    db.flush()
    return {"user_id": str(user.id), "pin_locked": False, "message": "Account unlocked"}


@router.get("/security/sessions")
def list_active_sessions(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    from api.models.user import UserSession
    try:
        user_id = uuid.UUID(str(current_user["sub"]))
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid user context")
    sessions = db.query(UserSession).filter_by(user_id=user_id, is_active=True).all()
    return {
        "sessions": [
            {"jti": session.token_jti, "created_at": str(session.created_at)}
            for session in sessions
        ]
    }
