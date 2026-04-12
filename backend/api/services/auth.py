"""
api/services/auth.py

Business logic สำหรับ Authentication:
- login: ตรวจสอบ credentials, สร้าง temporary token
- verify_pin: ตรวจสอบ PIN, สร้าง full JWT + UserSession
- forgot_pin / reset_pin: OTP flow
- forgot_password / reset_password: reset token flow
- change_password: change while logged in
- logout: invalidate session
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.models.user import User, PinOtp, PasswordResetToken, UserSession, LoginAttempt, PinAttempt
from api.utils.auth import (
    verify_password, verify_pin, hash_password, hash_pin,
    create_jwt_token,
)
from api.config import settings

# Constants
MAX_LOGIN_ATTEMPTS = 9         # block เมื่อมี failed attempts >= 9 (ครั้งที่ 10 ถูก block)
MAX_PIN_ATTEMPTS = 5           # lock หลัง 5 ครั้ง
MAX_OTP_REQUESTS = 3           # rate limit OTP ใน 60 วิ
OTP_WINDOW_SECONDS = 60
LOGIN_WINDOW_SECONDS = 900     # 15 นาที
TEMP_TOKEN_MINUTES = 5


def _count_recent_login_attempts(db: Session, email: str, window_seconds: int) -> int:
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    return (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.email == email,
            LoginAttempt.attempted_at >= cutoff,
            LoginAttempt.success == False,
        )
        .count()
    )


def _count_recent_pin_attempts(db: Session, user_id, window_seconds: int = 900) -> int:
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    return (
        db.query(PinAttempt)
        .filter(
            PinAttempt.user_id == user_id,
            PinAttempt.attempted_at >= cutoff,
            PinAttempt.success == False,
        )
        .count()
    )


def login(email: str, password: str, db: Session) -> dict:
    """
    Step 1 ของ auth flow: ตรวจสอบ email + password
    คืน temporary_token ที่ใช้ได้แค่ /auth/pin/verify
    """
    # Rate limiting: ตรวจสอบ failed attempts
    failed_count = _count_recent_login_attempts(db, email, LOGIN_WINDOW_SECONDS)
    if failed_count >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again later.",
        )

    user = db.query(User).filter_by(email=email, is_active=True).first()

    if not user or not verify_password(password, user.password_hash):
        # บันทึก failed attempt
        db.add(LoginAttempt(email=email, success=False))
        db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Login สำเร็จ — บันทึก success attempt
    db.add(LoginAttempt(email=email, success=True))
    db.flush()

    # สร้าง temporary token (pin_verified=False, is_temporary=True)
    temp_token = create_jwt_token(
        user_id=str(user.id),
        role=user.role,
        partner_id=str(user.partner_id),
        branch_id=str(user.branch_id) if user.branch_id else None,
        pin_verified=False,
        is_temporary=True,
        expires_delta=timedelta(minutes=TEMP_TOKEN_MINUTES),
    )

    return {"temporary_token": temp_token}


def verify_pin_and_issue_token(temp_token_payload: dict, pin: str, db: Session) -> dict:
    """
    Step 2 ของ auth flow: ตรวจสอบ PIN แล้วออก full JWT + สร้าง UserSession
    """
    import uuid as _uuid
    user_id = _uuid.UUID(str(temp_token_payload["sub"]))
    user = db.query(User).filter_by(id=user_id, is_active=True).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # ตรวจสอบว่า account ถูก lock หรือไม่
    if user.pin_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account locked due to too many wrong PIN attempts",
        )

    # ตรวจสอบ PIN
    if not user.pin_hash or not verify_pin(pin, user.pin_hash):
        # บันทึก failed attempt
        db.add(PinAttempt(user_id=user.id, success=False))
        db.flush()

        # นับ failed attempts (ไม่มี window — นับทั้งหมดหลัง last success)
        failed = _count_recent_pin_attempts(db, user.id)
        if failed >= MAX_PIN_ATTEMPTS:
            user.pin_locked = True
            db.flush()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many wrong PIN attempts",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN",
        )

    # PIN ถูก — บันทึก success
    db.add(PinAttempt(user_id=user.id, success=True))
    db.flush()

    # สร้าง full JWT
    access_token = create_jwt_token(
        user_id=str(user.id),
        role=user.role,
        partner_id=str(user.partner_id),
        branch_id=str(user.branch_id) if user.branch_id else None,
        pin_verified=True,
        is_temporary=False,
    )

    # decode เพื่อดึง jti + exp
    from api.utils.auth import decode_jwt_token
    payload = decode_jwt_token(access_token)
    jti = payload["jti"]
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)

    # สร้าง UserSession เพื่อ track token
    db.add(UserSession(
        user_id=user.id,
        token_jti=jti,
        expires_at=expires_at,
        is_active=True,
        email=user.email,
    ))
    db.flush()

    return {"access_token": access_token, "token_type": "bearer"}


def logout(token_payload: dict, db: Session) -> dict:
    """Invalidate UserSession โดย mark is_active=False"""
    import uuid as _uuid
    jti = token_payload.get("jti")
    if jti:
        session = db.query(UserSession).filter_by(token_jti=jti).first()
        if session:
            session.is_active = False
            db.flush()
        else:
            # ไม่มี session record → สร้าง invalidation record เพื่อป้องกันการใช้ token ซ้ำ
            user_id_str = token_payload.get("sub")
            if user_id_str:
                try:
                    user_id = _uuid.UUID(str(user_id_str))
                except (ValueError, AttributeError):
                    user_id = None
                if user_id:
                    exp = token_payload.get("exp", 0)
                    try:
                        from datetime import timezone
                        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)
                    except (OSError, ValueError, OverflowError):
                        expires_at = datetime.utcnow() + timedelta(hours=8)
                    user = db.query(User).filter_by(id=user_id).first()
                    email = user.email if user else "invalidated@logout"
                    db.add(UserSession(
                        user_id=user_id,
                        token_jti=jti,
                        expires_at=expires_at,
                        is_active=False,
                        email=email,
                    ))
                    db.flush()
    return {"message": "Logged out successfully"}


def forgot_pin(email: str, db: Session) -> dict:
    """
    ขอ OTP เพื่อ reset PIN
    Rate limit: ไม่เกิน MAX_OTP_REQUESTS ใน OTP_WINDOW_SECONDS
    """
    user = db.query(User).filter_by(email=email, is_active=True).first()

    if user:
        # นับ OTP requests ล่าสุด
        cutoff = datetime.utcnow() - timedelta(seconds=OTP_WINDOW_SECONDS)
        recent_count = (
            db.query(PinOtp)
            .filter(PinOtp.user_id == user.id, PinOtp.created_at >= cutoff)
            .count()
        )
        if recent_count >= MAX_OTP_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Try again later.",
            )

        # สร้าง OTP (ใน test env ใช้ค่าคงที่ "654321")
        otp_value = "654321" if settings.ENVIRONMENT in ("test", "development") else _generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        db.add(PinOtp(
            user_id=user.id,
            otp_hash=hash_pin(otp_value),
            expires_at=expires_at,
            used=False,
        ))
        db.flush()

    # ไม่เปิดเผยว่า email มีอยู่หรือไม่
    return {"message": "If the email exists, an OTP has been sent"}


def reset_pin(otp: str, new_pin: str, db: Session) -> dict:
    """Reset PIN ด้วย OTP"""
    # หา OTP ที่ยังไม่หมดอายุและยังไม่ได้ใช้
    records = db.query(PinOtp).filter_by(used=False).all()

    matching = None
    for record in records:
        if datetime.utcnow() > record.expires_at:
            continue
        try:
            if verify_pin(otp, record.otp_hash):
                matching = record
                break
        except Exception:
            continue

    if not matching:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is expired or invalid",
        )

    user = db.query(User).filter_by(id=matching.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.pin_hash = hash_pin(new_pin)
    user.pin_locked = False
    matching.used = True
    db.flush()

    return {"message": "PIN updated successfully"}


def forgot_password(email: str, db: Session) -> dict:
    """
    ขอ reset password token
    ไม่เปิดเผยว่า email มีอยู่หรือไม่ (anti-enumeration)
    """
    user = db.query(User).filter_by(email=email, is_active=True).first()

    if user:
        token_value = "test_reset_token" if settings.ENVIRONMENT in ("test", "development") else _generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hash_password(token_value),
            expires_at=expires_at,
            used=False,
        ))
        db.flush()

    return {"message": "If the email exists, a reset link has been sent"}


def reset_password(token: str, new_password: str, db: Session) -> dict:
    """Reset password ด้วย reset token"""
    records = db.query(PasswordResetToken).filter_by(used=False).all()

    matching = None
    for record in records:
        if datetime.utcnow() > record.expires_at:
            continue
        try:
            if verify_password(token, record.token_hash):
                matching = record
                break
        except Exception:
            continue

    if not matching:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is expired or invalid",
        )

    user = db.query(User).filter_by(id=matching.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.password_hash = hash_password(new_password)
    matching.used = True
    db.flush()

    return {"message": "Password updated successfully"}


def change_password(user_id, old_password: str, new_password: str, db: Session) -> dict:
    """เปลี่ยน password ขณะ login อยู่"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user or not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    user.password_hash = hash_password(new_password)
    db.flush()
    return {"message": "Password changed successfully"}


def assign_password(user_id, new_password: str, db: Session) -> dict:
    """Force-assign password (developer-only internal endpoint)"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(new_password)
    db.flush()
    return {"message": "Password assigned successfully"}


def assign_pin(user_id, new_pin: str, db: Session) -> dict:
    """Force-assign PIN + unlock account (developer-only internal endpoint)"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.pin_hash = hash_pin(new_pin)
    user.pin_locked = False
    db.flush()
    return {"message": "PIN assigned and account unlocked"}


def get_me(user_id, db: Session) -> dict:
    """ดึงข้อมูล current user"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "partner_id": str(user.partner_id),
        "branch_id": str(user.branch_id) if user.branch_id else None,
    }


def invalidate_all_sessions(db: Session) -> dict:
    """ดีด session ทุกคนออก — ต้อง login + verify PIN ใหม่ทั้งหมด"""
    from api.models.user import UserSession
    updated = db.query(UserSession).filter_by(is_active=True).update({"is_active": False})
    db.flush()
    return {"invalidated_sessions": updated}


def _generate_otp() -> str:
    import random
    return str(random.randint(100000, 999999))


def _generate_reset_token() -> str:
    import secrets
    return secrets.token_urlsafe(32)
