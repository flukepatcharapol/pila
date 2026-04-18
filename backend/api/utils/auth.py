"""
api/utils/auth.py

Utility functions สำหรับ authentication:
- hash_password / verify_password : bcrypt
- hash_pin / verify_pin           : bcrypt
- create_jwt_token                : JWT สำหรับ user session
- decode_jwt_token                : decode และ verify JWT
"""
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from api.config import settings


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def hash_pin(plain_pin: str) -> str:
    return bcrypt.hashpw(plain_pin.encode(), bcrypt.gensalt()).decode()


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    return bcrypt.checkpw(plain_pin.encode(), hashed_pin.encode())


def create_jwt_token(
    user_id: str,
    role: str,
    partner_id: str,
    branch_ids: list | None = None,
    pin_verified: bool = False,
    expires_delta: timedelta | None = None,
    is_temporary: bool = False,
    **_legacy,
) -> str:
    """
    สร้าง JWT token (multi-branch edition).

    branch_ids:
      None       → unrestricted (DEVELOPER/OWNER)
      list[str]  → this user may only access these branches

    - pin_verified=False  → temporary token (ใช้แค่ /auth/pin/verify)
    - pin_verified=True   → full access token
    - is_temporary=True   → mark เป็น temp token เพื่อ block access endpoints

    NOTE: legacy `branch_id=` kwarg is tolerated and wrapped into a single-item
    list, to keep older call sites compiling during the refactor. It will be
    removed once all callers pass branch_ids directly.
    """
    jti = str(uuid.uuid4())

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # tolerate legacy branch_id kwarg
    if branch_ids is None and "branch_id" in _legacy and _legacy["branch_id"]:
        branch_ids = [_legacy["branch_id"]]

    if branch_ids is None:
        encoded_branch_ids = None
    else:
        encoded_branch_ids = [str(b) for b in branch_ids if b is not None]

    payload = {
        "sub": str(user_id),
        "role": str(role),
        "partner_id": str(partner_id),
        "branch_ids": encoded_branch_ids,
        "pin_verified": pin_verified,
        "is_temporary": is_temporary,
        "jti": jti,
        "exp": expire,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """Decode JWT token — raises JWTError หาก invalid หรือ expired"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
