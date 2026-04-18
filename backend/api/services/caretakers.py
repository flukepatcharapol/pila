"""
api/services/caretakers.py

Business logic สำหรับ Caretaker CRUD
"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.trainer import Caretaker
from api.services.activity_log import log as activity_log
from api.dependencies.branch_scope import get_user_branch_ids, assert_branch_access

MAX_PAGE_SIZE = 100


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def _to_dict(caretaker: Caretaker) -> dict:
    return {
        "id": str(caretaker.id),
        "branch_id": str(caretaker.branch_id),
        "name": caretaker.name,
        "email": caretaker.email,
        "status": caretaker.status,
    }


def _apply_scope(query, current_user: dict):
    """Filter caretakers ตาม role (multi-branch)."""
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    allowed = get_user_branch_ids(current_user)

    if role == "DEVELOPER":
        pass
    elif role == "OWNER":
        from api.models.branch import Branch
        query = query.join(Branch, Caretaker.branch_id == Branch.id).filter(
            Branch.partner_id == _to_uuid(partner_id)
        )
    else:
        if allowed:
            query = query.filter(Caretaker.branch_id.in_(allowed))
        else:
            query = query.filter(Caretaker.id == uuid.UUID(int=0))

    return query


def list_caretakers(current_user: dict, db: Session, page: int = 1, page_size: int = 20) -> dict:
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size cannot exceed {MAX_PAGE_SIZE}")

    query = db.query(Caretaker)
    query = _apply_scope(query, current_user)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_to_dict(caretaker) for caretaker in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_caretaker(caretaker_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    caretaker = db.query(Caretaker).filter_by(id=caretaker_id).first()
    if not caretaker:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    return _to_dict(caretaker)


def create_caretaker(payload: dict, current_user: dict, db: Session) -> dict:
    """สร้าง caretaker — admin ทำได้เฉพาะ branch ตัวเอง"""
    branch_id = _to_uuid(payload["branch_id"])
    role = current_user.get("role", "")

    # Admin ต้องสร้าง caretaker เฉพาะ branch ที่ตัวเองเข้าถึงได้
    if role == "ADMIN":
        assert_branch_access(current_user, branch_id)

    caretaker = Caretaker(
        branch_id=branch_id,
        name=payload["name"],
        email=payload.get("email"),
        status=payload.get("status", "ACTIVE"),
    )
    db.add(caretaker)
    db.flush()

    activity_log(db, current_user, "caretaker.create", "caretaker", str(caretaker.id),
                 detail=f"Created caretaker: {payload['name']}")
    return _to_dict(caretaker)


def update_caretaker(caretaker_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    caretaker = db.query(Caretaker).filter_by(id=caretaker_id).first()
    if not caretaker:
        raise HTTPException(status_code=404, detail="Caretaker not found")

    before = _to_dict(caretaker)
    for field in ["name", "email", "status"]:
        if field in payload and payload[field] is not None:
            setattr(caretaker, field, payload[field])
    db.flush()

    activity_log(db, current_user, "caretaker.edit", "caretaker", str(caretaker_id),
                 changes={"before": before, "after": _to_dict(caretaker)})
    return _to_dict(caretaker)


def delete_caretaker(caretaker_id: uuid.UUID, current_user: dict, db: Session) -> None:
    caretaker = db.query(Caretaker).filter_by(id=caretaker_id).first()
    if not caretaker:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    db.delete(caretaker)
    db.flush()
    activity_log(db, current_user, "caretaker.delete", "caretaker", str(caretaker_id))
