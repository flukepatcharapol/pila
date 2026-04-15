"""
api/services/bookings.py

Business logic สำหรับ Booking lifecycle
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.booking import Booking
from api.models.trainer import Trainer
from api.services.activity_log import log as activity_log

MAX_PAGE_SIZE = 100


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def _booking_to_dict(booking: Booking) -> dict:
    """แปลง Booking ORM → dict พร้อม fields ทั้งหมด"""
    return {
        "id": str(booking.id),
        "branch_id": str(booking.branch_id),
        "trainer_id": str(booking.trainer_id) if booking.trainer_id else None,
        "customer_id": str(booking.customer_id) if booking.customer_id else None,
        "caretaker_id": str(booking.caretaker_id) if booking.caretaker_id else None,
        "booking_type": booking.booking_type,
        "booking_source": booking.booking_source,
        "start_time": str(booking.start_time),
        "end_time": str(booking.end_time),
        "status": booking.status,
        "notes": booking.notes,
        "line_notified": booking.line_notified,
        "hour_returned": booking.hour_returned,
        "confirmed_by": str(booking.confirmed_by) if booking.confirmed_by else None,
        "confirmed_at": str(booking.confirmed_at) if booking.confirmed_at else None,
        "cancelled_by": str(booking.cancelled_by) if booking.cancelled_by else None,
        "cancelled_at": str(booking.cancelled_at) if booking.cancelled_at else None,
        "cancel_reason": booking.cancel_reason,
        "created_at": str(booking.created_at),
    }


def _apply_scope(query, current_user: dict):
    """กรอง bookings ตาม role"""
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    branch_id = current_user.get("branch_id")
    if role == "DEVELOPER":
        pass
    elif role == "OWNER":
        # owner เห็นทุก branch ใน partner — join ผ่าน Branch
        from api.models.branch import Branch
        query = query.join(Branch, Booking.branch_id == Branch.id).filter(
            Branch.partner_id == _to_uuid(partner_id)
        )
    else:
        # BRANCH_MASTER, ADMIN, TRAINER — เห็นแค่ branch ตัวเอง
        if branch_id:
            query = query.filter(Booking.branch_id == _to_uuid(branch_id))
    return query


def list_bookings(current_user: dict, db: Session, page: int = 1, page_size: int = 20,
                  trainer_id: str = None, date: str = None,
                  start_date: str = None, end_date: str = None) -> dict:
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size cannot exceed {MAX_PAGE_SIZE}")

    role = current_user.get("role", "")
    # Check permission matrix — default allow if no record
    from api.services.permissions import check_permission
    if role not in ("DEVELOPER",) and not check_permission(db, role, "booking", "VIEW"):
        raise HTTPException(status_code=403, detail="Forbidden")

    query = db.query(Booking)
    query = _apply_scope(query, current_user)
    if trainer_id:
        query = query.filter(Booking.trainer_id == _to_uuid(trainer_id))
    if date:
        query = query.filter(
            Booking.start_time >= datetime.fromisoformat(f"{date}T00:00:00"),
            Booking.start_time <= datetime.fromisoformat(f"{date}T23:59:59"),
        )
    if start_date:
        query = query.filter(Booking.start_time >= datetime.fromisoformat(f"{start_date}T00:00:00"))
    if end_date:
        query = query.filter(Booking.start_time <= datetime.fromisoformat(f"{end_date}T23:59:59"))
    total = query.count()
    items = query.order_by(Booking.start_time).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_booking_to_dict(booking) for booking in items], "total": total, "page": page, "page_size": page_size}


def get_booking(booking_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return _booking_to_dict(booking)


def create_booking(payload: dict, current_user: dict, db: Session) -> dict:
    """สร้าง booking — trainer optional สำหรับ external booking"""
    branch_id = _to_uuid(payload["branch_id"])
    trainer_id = _to_uuid(payload.get("trainer_id"))
    role = current_user.get("role", "").upper()

    # TRAINER role: can only book with own user ID as trainer_id
    if role == "TRAINER":
        current_sub = current_user.get("sub")
        if trainer_id is not None and str(trainer_id) != str(current_sub):
            raise HTTPException(status_code=403, detail="Forbidden")
        # Store trainer_id as None (User ID ≠ Trainer entity ID)
        trainer_id = None
    elif trainer_id:
        # ตรวจสอบว่า trainer อยู่ใน branch เดียวกัน (ถ้ามี trainer)
        trainer = db.query(Trainer).filter_by(id=trainer_id).first()
        if not trainer or trainer.branch_id != branch_id:
            raise HTTPException(status_code=400, detail="Trainer does not belong to the specified branch")

    booking = Booking(
        branch_id=branch_id,
        trainer_id=trainer_id,
        customer_id=_to_uuid(payload.get("customer_id")),
        caretaker_id=_to_uuid(payload.get("caretaker_id")),
        start_time=datetime.fromisoformat(payload["start_time"]),
        end_time=datetime.fromisoformat(payload["end_time"]),
        booking_type=payload.get("booking_type", "CUSTOMER"),
        booking_source=payload.get("booking_source", "INTERNAL"),
        status="PENDING",
        notes=payload.get("notes"),
        created_by=_to_uuid(current_user.get("sub")),
    )
    db.add(booking)
    db.flush()

    activity_log(db, current_user, "booking.create", "booking", str(booking.id))
    return _booking_to_dict(booking)


def update_booking(booking_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    before = _booking_to_dict(booking)
    for field in ["notes", "start_time", "end_time"]:
        if field in payload:
            val = payload[field]
            if field in ("start_time", "end_time") and isinstance(val, str):
                val = datetime.fromisoformat(val)
            setattr(booking, field, val)
    db.flush()

    activity_log(db, current_user, "booking.update", "booking", str(booking_id),
                 changes={"before": before, "after": _booking_to_dict(booking)})
    return _booking_to_dict(booking)


def delete_booking(booking_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    """Cancel booking — mark CANCELLED แทนการลบ, คืน dict"""
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "CANCELLED"
    booking.cancelled_by = _to_uuid(current_user.get("sub"))
    booking.cancelled_at = datetime.utcnow()
    db.flush()

    activity_log(db, current_user, "booking.cancel", "booking", str(booking_id))
    return _booking_to_dict(booking)
