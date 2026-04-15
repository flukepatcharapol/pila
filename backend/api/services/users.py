"""api/services/users.py"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.user import User
from api.utils.auth import hash_password, hash_pin
from api.services.activity_log import log as activity_log

# Role hierarchy for access control
ROLE_HIERARCHY = ["TRAINER", "ADMIN", "BRANCH_MASTER", "OWNER", "DEVELOPER"]
ROLE_RANK = {role: rank_index for rank_index, role in enumerate(ROLE_HIERARCHY)}


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def _user_to_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "partner_id": str(user.partner_id),
        "branch_id": str(user.branch_id) if user.branch_id else None,
        "is_active": user.is_active,
        "pin_locked": user.pin_locked,
    }


def list_users(current_user: dict, db: Session, page: int = 1, page_size: int = 20) -> dict:
    query = db.query(User)
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    branch_id = current_user.get("branch_id")

    if role == "DEVELOPER":
        pass
    elif role == "OWNER":
        query = query.filter(User.partner_id == _to_uuid(partner_id))
    elif role == "BRANCH_MASTER":
        query = query.filter(User.branch_id == _to_uuid(branch_id))
    else:
        query = query.filter(User.partner_id == _to_uuid(partner_id))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_user_to_dict(user) for user in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_user(user_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_dict(user)


def _check_create_permission(current_user: dict, payload: dict, db: Session):
    """ตรวจสอบว่า current_user มีสิทธิ์สร้าง user ด้วย role และ branch ที่ระบุ"""
    role = current_user.get("role", "").upper()
    current_rank = ROLE_RANK.get(role, -1)

    # ADMIN และต่ำกว่า ไม่สามารถสร้าง user ได้
    if role not in ("DEVELOPER", "OWNER", "BRANCH_MASTER"):
        raise HTTPException(status_code=403, detail="Forbidden")

    target_role = payload.get("role", "ADMIN").upper()
    target_rank = ROLE_RANK.get(target_role, -1)

    # ไม่สามารถสร้าง role ที่เท่ากับหรือสูงกว่าตัวเอง
    if target_rank >= current_rank:
        raise HTTPException(status_code=403, detail="Cannot create user with equal or higher role")

    # BRANCH_MASTER ต้องสร้างเฉพาะ branch ตัวเอง
    if role == "BRANCH_MASTER":
        my_branch_id = str(current_user.get("branch_id", ""))
        target_branch_id = str(payload.get("branch_id", ""))
        if my_branch_id and target_branch_id and my_branch_id != target_branch_id:
            raise HTTPException(status_code=403, detail="Cannot create user in another branch")


def create_user(payload: dict, current_user: dict, db: Session) -> dict:
    _check_create_permission(current_user, payload, db)

    existing = db.query(User).filter_by(email=payload["email"]).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    partner_id = _to_uuid(current_user.get("partner_id"))
    user = User(
        partner_id=partner_id,
        branch_id=_to_uuid(payload.get("branch_id")),
        username=payload["username"],
        email=payload["email"],
        password_hash=hash_password(payload.get("password", "changeme")),
        pin_hash=hash_pin(payload.get("pin", "000000")) if payload.get("pin") else None,
        role=payload.get("role", "ADMIN"),
        is_active=payload.get("is_active", True),
    )
    db.add(user)
    db.flush()

    activity_log(db, current_user, "user.create", "user", str(user.id),
                 detail=f"Created user: {payload['username']}")
    return _user_to_dict(user)


def update_user(user_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field in ["username", "email", "role", "is_active", "branch_id"]:
        if field in payload:
            setattr(user, field, payload[field])
    if payload.get("password"):
        user.password_hash = hash_password(payload["password"])
    db.flush()
    return _user_to_dict(user)


def change_user_role(user_id: uuid.UUID, new_role: str, current_user: dict, db: Session) -> dict:
    """เปลี่ยน role ของ user — เฉพาะ OWNER+ เท่านั้น และ target role ต้องต่ำกว่า current"""
    role = current_user.get("role", "").upper()
    current_rank = ROLE_RANK.get(role, -1)

    # Only OWNER+ can change roles
    if role not in ("DEVELOPER", "OWNER"):
        raise HTTPException(status_code=403, detail="Forbidden")

    new_role_upper = new_role.upper()
    new_rank = ROLE_RANK.get(new_role_upper, -1)

    # Cannot elevate to role >= own level
    if new_rank >= current_rank:
        raise HTTPException(status_code=403, detail="Cannot assign equal or higher role")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = new_role_upper
    db.flush()

    activity_log(db, current_user, "user.role_change", "user", str(user_id),
                 detail=f"Changed role to {new_role_upper}")
    return _user_to_dict(user)


def delete_user(user_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    """Soft-delete: set is_active=False ไม่ลบจริง"""
    current_sub = str(current_user.get("sub", ""))

    # Cannot deactivate own account
    if current_sub and current_sub == str(user_id):
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    role = current_user.get("role", "").upper()
    current_rank = ROLE_RANK.get(role, -1)

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cannot deactivate user with higher or equal role
    target_rank = ROLE_RANK.get(user.role.upper(), -1)
    if target_rank >= current_rank:
        raise HTTPException(status_code=403, detail="Cannot deactivate user with equal or higher role")

    user.is_active = False
    db.flush()

    activity_log(db, current_user, "user.deactivate", "user", str(user_id))
    return _user_to_dict(user)
