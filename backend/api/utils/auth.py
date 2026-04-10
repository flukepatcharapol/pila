"""
api/utils/auth.py

Utility functions สำหรับ authentication:
- hash_password: เปลี่ยน plain password เป็น bcrypt hash
- verify_password: ตรวจสอบ password กับ hash
- create_jwt_token: สร้าง JWT token สำหรับ user session
"""
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt

from api.config import settings


# bcrypt context สำหรับ hash/verify passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """เปลี่ยน plain password เป็น bcrypt hash ก่อน store ใน DB"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ตรวจสอบว่า password ตรงกับ hash ใน DB หรือไม่"""
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    สร้าง JWT token
    - data: payload ที่จะ encode (เช่น {"sub": user_id, "role": role})
    - expires_delta: อายุ token (default ตาม settings)
    """
    to_encode = data.copy()

    # คำนวณ expiry time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode["exp"] = expire

    # encode ด้วย secret key
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
