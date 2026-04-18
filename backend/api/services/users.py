"""api/services/users.py"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.user import User
from api.models.branch import Branch
from api.utils.auth import hash_password, hash_pin
from api.services.activity_log import log as activity_log
from api.dependencies.branch_scope import get_user_branch_ids

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
    scoped = get_user_branch_ids(user)
    if scoped is None:
        branch_ids: list[str] | None = None
    else:
        branch_ids = [str(b) for b in scoped]
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "partner_id": str(user.partner_id),
        "branch_ids": branch_ids,
        "is_active": user.is_active,
        "pin_locked": user.pin_locked,
    }


def list_users(current_user: dict, db: Session, page: int = 1, page_size: int = 20) -> dict:
    query = db.query(User)
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    allowed_branches = get_user_branch_ids(current_user)

    if role == "DEVELOPER":
        pass
    elif role == "OWNER":
        query = query.filter(User.partner_id == _to_uuid(partner_id))
    elif role == "BRANCH_MASTER":
        # List only users who share at least one branch with the branch_master.
        if allowed_branches:
            query = (
                query.filter(User.partner_id == _to_uuid(partner_id))
                     .filter(User.branches.any(Branch.id.in_(allowed_branches)))
            )
        else:
            # No branches assigned → see nobody (except self by partner scope)
            query = query.filter(User.partner_id == _to_uuid(partner_id))
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


def _resolve_branch_ids_from_payload(payload: dict) -> list[uuid.UUID]:
    """Accept branch_ids (list or single value)."""
    if payload.get("branch_ids") is not None:
        raw = payload["branch_ids"]
    else:
        raw = []

    # Be tolerant to clients that send one branch as scalar instead of array.
    if isinstance(raw, (str, uuid.UUID)):
        items = [raw]
    elif isinstance(raw, (list, tuple, set)):
        items = list(raw)
    else:
        items = []

    resolved: list[uuid.UUID] = []
    for v in items:
        u = _to_uuid(v)
        if u is None:
            raise HTTPException(status_code=400, detail=f"Invalid branch id: {v}")
        if u not in resolved:
            resolved.append(u)
    return resolved


def _check_create_permission(current_user: dict, payload: dict, branch_ids: list, db: Session):
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

    # Role-level branch requirements
    if target_role in ("BRANCH_MASTER", "ADMIN", "TRAINER") and not branch_ids:
        raise HTTPException(status_code=400, detail="branch_ids is required for this role")

    # All target branches must belong to the actor's partner
    actor_partner_id = _to_uuid(current_user.get("partner_id"))
    if branch_ids and actor_partner_id:
        owned_ids = {
            bid for (bid,) in db.query(Branch.id)
                                 .filter(Branch.id.in_(branch_ids),
                                         Branch.partner_id == actor_partner_id)
                                 .all()
        }
        missing = [b for b in branch_ids if b not in owned_ids]
        if missing:
            raise HTTPException(status_code=403, detail="One or more branch_ids are outside your partner")

    # BRANCH_MASTER may only assign branches they themselves belong to
    if role == "BRANCH_MASTER":
        my_branch_ids = set(get_user_branch_ids(current_user) or [])
        for target_bid in branch_ids:
            if target_bid not in my_branch_ids:
                raise HTTPException(status_code=403, detail="Cannot create user in another branch")


def create_user(payload: dict, current_user: dict, db: Session) -> dict:
    branch_ids = _resolve_branch_ids_from_payload(payload)
    _check_create_permission(current_user, payload, branch_ids, db)

    existing = db.query(User).filter_by(email=payload["email"]).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    partner_id = _to_uuid(current_user.get("partner_id"))
    user = User(
        partner_id=partner_id,
        username=payload["username"],
        email=payload["email"],
        password_hash=hash_password(payload.get("password", "changeme")),
        pin_hash=hash_pin(payload.get("pin", "000000")) if payload.get("pin") else None,
        role=payload.get("role", "ADMIN"),
        is_active=payload.get("is_active", True),
    )
    # Attach branches (many-to-many)
    if branch_ids:
        attached = db.query(Branch).filter(Branch.id.in_(branch_ids)).all()
        user.branches = attached
    db.add(user)
    db.flush()

    activity_log(db, current_user, "user.create", "user", str(user.id),
                 detail=f"Created user: {payload['username']}")
    return _user_to_dict(user)


def update_user(user_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field in ["username", "email", "role", "is_active"]:
        if field in payload:
            setattr(user, field, payload[field])
    # Multi-branch update: accept branch_ids only
    if "branch_ids" in payload:
        branch_ids = _resolve_branch_ids_from_payload(payload)
        if branch_ids:
            attached = db.query(Branch).filter(Branch.id.in_(branch_ids)).all()
            user.branches = attached
        else:
            user.branches = []
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
