"""
api/routers/auth.py

Authentication endpoints:
  POST /auth/login
  POST /auth/pin/verify
  POST /auth/pin/forgot
  POST /auth/pin/reset
  POST /auth/password/forgot
  POST /auth/password/reset
  POST /auth/password/change  (protected)
  POST /auth/logout            (protected)
  GET  /auth/me                (protected)
  POST /internal/assign-password/:user_id
  POST /internal/assign-pin/:user_id
"""
import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import JWTError

from api.database import get_db
from api.utils.auth import decode_jwt_token
from api.dependencies.auth import require_pin_verified, get_developer_api_key, bearer_scheme
from api.services import auth as auth_service
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()


# ─── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class PinVerifyRequest(BaseModel):
    pin: str

class PinForgotRequest(BaseModel):
    email: str

class PinResetRequest(BaseModel):
    otp: str
    new_pin: str

class PasswordForgotRequest(BaseModel):
    email: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class AssignPasswordRequest(BaseModel):
    new_password: str

class AssignPinRequest(BaseModel):
    new_pin: str


# ─── Helper: ดึง temp token payload ────────────────────────────────────────────

def _get_temp_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """Extract payload จาก temporary token (ยังไม่ต้อง pin_verified)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = decode_jwt_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(body.email, body.password, db)


@router.post("/auth/pin/verify")
def pin_verify(
    body: PinVerifyRequest,
    payload: dict = Depends(_get_temp_token_payload),
    db: Session = Depends(get_db),
):
    return auth_service.verify_pin_and_issue_token(payload, body.pin, db)


@router.post("/auth/pin/forgot")
def pin_forgot(body: PinForgotRequest, db: Session = Depends(get_db)):
    return auth_service.forgot_pin(body.email, db)


@router.post("/auth/pin/reset")
def pin_reset(body: PinResetRequest, db: Session = Depends(get_db)):
    return auth_service.reset_pin(body.otp, body.new_pin, db)


@router.post("/auth/password/forgot")
def password_forgot(body: PasswordForgotRequest, db: Session = Depends(get_db)):
    return auth_service.forgot_password(body.email, db)


@router.post("/auth/password/reset")
def password_reset(body: PasswordResetRequest, db: Session = Depends(get_db)):
    return auth_service.reset_password(body.token, body.new_password, db)


@router.post("/auth/password/change")
def password_change(
    body: PasswordChangeRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    try:
        user_id = uuid.UUID(str(current_user["sub"]))
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid user context")
    return auth_service.change_password(user_id, body.old_password, body.new_password, db)


@router.post("/auth/logout")
def logout(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return auth_service.logout(current_user, db)


@router.get("/auth/me")
def get_me(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    try:
        user_id = uuid.UUID(str(current_user["sub"]))
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid user context")
    return auth_service.get_me(user_id, db)


# ─── Internal Developer-only ───────────────────────────────────────────────────

@router.post("/internal/assign-password/{user_id}")
def internal_assign_password(
    user_id: UUID,
    body: AssignPasswordRequest,
    _: str = Depends(get_developer_api_key),
    db: Session = Depends(get_db),
):
    return auth_service.assign_password(user_id, body.new_password, db)


@router.post("/internal/assign-pin/{user_id}")
def internal_assign_pin(
    user_id: UUID,
    body: AssignPinRequest,
    _: str = Depends(get_developer_api_key),
    db: Session = Depends(get_db),
):
    return auth_service.assign_pin(user_id, body.new_pin, db)


@router.post("/internal/invalidate-all-sessions")
def internal_invalidate_all_sessions(
    _: str = Depends(get_developer_api_key),
    db: Session = Depends(get_db),
):
    return auth_service.invalidate_all_sessions(db)
