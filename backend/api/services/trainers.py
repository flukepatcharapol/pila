"""
api/services/trainers.py

Business logic สำหรับ Trainer CRUD
"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.trainer import Trainer
from api.models.customer import Customer
from api.models.booking import Booking
from api.services.activity_log import log as activity_log

MAX_PAGE_SIZE = 100


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def _to_dict(trainer: Trainer) -> dict:
    """แปลง Trainer ORM object → dict สำหรับ API response"""
    return {
        "id": str(trainer.id),
        "branch_id": str(trainer.branch_id),
        "name": trainer.name,
        "display_name": trainer.display_name,
        "email": trainer.email,
        "profile_photo_url": trainer.profile_photo_url,
        "status": trainer.status,
    }


def _apply_scope(query, current_user: dict):
    """Filter trainers ตาม role — admin/trainer เห็นแค่ branch ตัวเอง (multi-branch)."""
    from api.dependencies.branch_scope import get_user_branch_ids
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    allowed = get_user_branch_ids(current_user)

    if role == "DEVELOPER":
        pass  # เห็นทุก trainer ในทุก partner
    elif role == "OWNER":
        from api.models.branch import Branch
        query = query.join(Branch, Trainer.branch_id == Branch.id).filter(
            Branch.partner_id == _to_uuid(partner_id)
        )
    else:
        if allowed:
            query = query.filter(Trainer.branch_id.in_(allowed))
        else:
            query = query.filter(Trainer.id == uuid.UUID(int=0))

    return query


def list_trainers(current_user: dict, db: Session, page: int = 1, page_size: int = 20,
                  status: str = None) -> dict:
    """List trainers พร้อม pagination + scope filter"""
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size cannot exceed {MAX_PAGE_SIZE}")

    query = db.query(Trainer)
    query = _apply_scope(query, current_user)

    if status:
        query = query.filter(Trainer.status == status.upper())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_to_dict(trainer) for trainer in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_trainer(trainer_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    trainer = db.query(Trainer).filter_by(id=trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return _to_dict(trainer)


def create_trainer(payload: dict, current_user: dict, db: Session) -> dict:
    """สร้าง trainer — auto-generate display_name = "name:branch_prefix" ถ้าไม่ระบุ"""
    branch_id = _to_uuid(payload["branch_id"])

    # ดึง branch prefix เพื่อ auto-generate display_name
    from api.models.branch import Branch
    branch = db.query(Branch).filter_by(id=branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    name = payload["name"]
    # display_name: "Name:BranchPrefix" — ใช้แสดงใน dropdown เพื่อแยก trainer ต่าง branch
    display_name = payload.get("display_name") or f"{name}:{branch.prefix}"

    trainer = Trainer(
        branch_id=branch_id,
        name=name,
        display_name=display_name,
        email=payload.get("email"),
        profile_photo_url=payload.get("profile_photo_url"),
        status=payload.get("status", "ACTIVE"),
    )
    db.add(trainer)
    db.flush()

    activity_log(db, current_user, "trainer.create", "trainer", str(trainer.id),
                 detail=f"Created trainer: {name}")
    return _to_dict(trainer)


def update_trainer(trainer_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    trainer = db.query(Trainer).filter_by(id=trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")

    before = _to_dict(trainer)
    for field in ["name", "display_name", "email", "profile_photo_url", "status"]:
        if field in payload and payload[field] is not None:
            setattr(trainer, field, payload[field])
    db.flush()

    activity_log(db, current_user, "trainer.edit", "trainer", str(trainer_id),
                 changes={"before": before, "after": _to_dict(trainer)})
    return _to_dict(trainer)


def delete_trainer(trainer_id: uuid.UUID, current_user: dict, db: Session) -> None:
    trainer = db.query(Trainer).filter_by(id=trainer_id).first()
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")

    # INT-04: ไม่ลบ trainer ที่ยังมี active customer อยู่
    active_customers = db.query(Customer).filter_by(trainer_id=trainer_id, status="ACTIVE").count()
    if active_customers > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete trainer with active customers",
        )

    # INT-04: ไม่ลบ trainer ที่ยังมี active booking อยู่
    active_bookings = db.query(Booking).filter(
        Booking.trainer_id == trainer_id,
        Booking.status.in_(["PENDING", "CONFIRMED", "pending", "confirmed"]),
    ).count()
    if active_bookings > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete trainer with active bookings",
        )

    db.delete(trainer)
    db.flush()
    activity_log(db, current_user, "trainer.delete", "trainer", str(trainer_id))
