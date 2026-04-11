"""
api/services/caretakers.py

Business logic สำหรับ Caretaker CRUD
"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.trainer import Caretaker
from api.services.activity_log import log as activity_log

MAX_PAGE_SIZE = 100


def _to_uuid(val) -> uuid.UUID | None:
    if not val:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _to_dict(c: Caretaker) -> dict:
    return {
        "id": str(c.id),
        "branch_id": str(c.branch_id),
        "name": c.name,
        "email": c.email,
        "status": c.status,
    }


def _apply_scope(query, current_user: dict):
    """Filter caretakers ตาม role"""
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    branch_id = current_user.get("branch_id")

    if role == "DEVELOPER":
        pass
    elif role == "OWNER":
        from api.models.branch import Branch
        query = query.join(Branch, Caretaker.branch_id == Branch.id).filter(
            Branch.partner_id == _to_uuid(partner_id)
        )
    else:
        if branch_id:
            query = query.filter(Caretaker.branch_id == _to_uuid(branch_id))

    return query


def list_caretakers(current_user: dict, db: Session, page: int = 1, page_size: int = 20) -> dict:
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size cannot exceed {MAX_PAGE_SIZE}")

    query = db.query(Caretaker)
    query = _apply_scope(query, current_user)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_to_dict(c) for c in items], "total": total, "page": page, "page_size": page_size}


def get_caretaker(caretaker_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    c = db.query(Caretaker).filter_by(id=caretaker_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    return _to_dict(c)


def create_caretaker(payload: dict, current_user: dict, db: Session) -> dict:
    """สร้าง caretaker — admin ทำได้เฉพาะ branch ตัวเอง"""
    branch_id = _to_uuid(payload["branch_id"])
    role = current_user.get("role", "")
    user_branch_id = _to_uuid(current_user.get("branch_id"))

    # ตรวจสอบว่า admin ไม่สร้าง caretaker ให้ branch อื่น
    if role == "ADMIN" and user_branch_id and user_branch_id != branch_id:
        raise HTTPException(status_code=403, detail="Admin can only create caretakers for own branch")

    c = Caretaker(
        branch_id=branch_id,
        name=payload["name"],
        email=payload.get("email"),
        status=payload.get("status", "ACTIVE"),
    )
    db.add(c)
    db.flush()

    activity_log(db, current_user, "caretaker.create", "caretaker", str(c.id),
                 detail=f"Created caretaker: {payload['name']}")
    return _to_dict(c)


def update_caretaker(caretaker_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    c = db.query(Caretaker).filter_by(id=caretaker_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Caretaker not found")

    before = _to_dict(c)
    for field in ["name", "email", "status"]:
        if field in payload and payload[field] is not None:
            setattr(c, field, payload[field])
    db.flush()

    activity_log(db, current_user, "caretaker.edit", "caretaker", str(caretaker_id),
                 changes={"before": before, "after": _to_dict(c)})
    return _to_dict(c)


def delete_caretaker(caretaker_id: uuid.UUID, current_user: dict, db: Session) -> None:
    c = db.query(Caretaker).filter_by(id=caretaker_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    db.delete(c)
    db.flush()
    activity_log(db, current_user, "caretaker.delete", "caretaker", str(caretaker_id))
