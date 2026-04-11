"""
api/dependencies/auth.py

FastAPI dependencies สำหรับ authentication และ authorization:
- get_current_user   : ดึง user จาก JWT token
- require_pin_verified : ตรวจสอบว่า token ผ่าน PIN แล้ว
- require_role       : ตรวจสอบ role
- get_developer_api_key : ตรวจสอบ Developer API Key
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError
from sqlalchemy.orm import Session

from api.database import get_db
from api.utils.auth import decode_jwt_token
from api.config import settings

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """
    Dependency: ดึง current user จาก JWT token
    คืน payload dict ที่มี user_id, role, partner_id, branch_id, pin_verified
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_jwt_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ตรวจสอบว่า session ไม่ถูก invalidate (logout)
    # ถ้า session record มีอยู่และ is_active=False → ถูก logout แล้ว
    # ถ้าไม่มี session record → token ยังใช้ได้ (เช่น test tokens หรือ tokens ก่อน session tracking)
    jti = payload.get("jti")
    if jti:
        from api.models.user import UserSession
        session = db.query(UserSession).filter_by(token_jti=jti).first()
        if session and not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return payload


def require_pin_verified(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Dependency: ตรวจสอบว่า token ผ่าน PIN verify แล้ว
    Temporary token (pre-PIN) ถูก reject ที่นี่
    """
    if not current_user.get("pin_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN verification required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.get("is_temporary"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Temporary token cannot access protected resources",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory: ตรวจสอบว่า user มี role ที่อนุญาต
    ใช้: Depends(require_role("OWNER", "BRANCH_MASTER"))
    """
    def _check(current_user: dict = Depends(require_pin_verified)) -> dict:
        role = current_user.get("role", "")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not allowed for this endpoint",
            )
        return current_user
    return _check


def get_developer_api_key(
    api_key: str | None = Depends(api_key_header),
) -> str:
    """Dependency: ตรวจสอบ Developer API Key สำหรับ /internal/* endpoints"""
    if not api_key or api_key != settings.DEVELOPER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Valid Developer API Key required",
        )
    return api_key
