"""
api/routers/bookings.py

Booking endpoints:
  GET  /bookings
  POST /bookings
  GET  /bookings/:id
  PUT  /bookings/:id
  DELETE /bookings/:id         — cancel
  PUT  /bookings/:id/confirm   — confirm pending booking
  POST /bookings/external      — external booking (API Key auth)
"""
import uuid
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import bookings as booking_service
from api.config import settings

router = APIRouter()


class CreateBookingRequest(BaseModel):
    branch_id: str
    trainer_id: Optional[str] = None
    customer_id: Optional[str] = None
    caretaker_id: Optional[str] = None
    start_time: str
    end_time: str
    booking_type: str = "CUSTOMER"
    notes: Optional[str] = None


class UpdateBookingRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ExternalBookingRequest(BaseModel):
    branch_id: str
    customer_id: str
    trainer_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    slots: Optional[int] = None          # number of 1-hour slots from start_time
    slot_times: Optional[List[str]] = None  # list of "HH:MM" times (must be contiguous)
    notes: Optional[str] = None


@router.get("/bookings")
def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    trainer_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return booking_service.list_bookings(
        current_user, db, page, page_size, trainer_id, date, start_date, end_date
    )


@router.post("/bookings", status_code=201)
def create_booking(
    body: CreateBookingRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return booking_service.create_booking(body.model_dump(), current_user, db)


@router.get("/bookings/{booking_id}")
def get_booking(
    booking_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return booking_service.get_booking(booking_id, current_user, db)


@router.put("/bookings/{booking_id}")
def update_booking(
    booking_id: UUID,
    body: UpdateBookingRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return booking_service.update_booking(booking_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/bookings/{booking_id}")
def cancel_booking(
    booking_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    role = current_user.get("role", "")
    if role == "TRAINER":
        raise HTTPException(status_code=403, detail="Forbidden")
    return booking_service.delete_booking(booking_id, current_user, db)


@router.put("/bookings/{booking_id}/confirm")
def confirm_booking(
    booking_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    Confirm booking PENDING → CONFIRMED
    บันทึก confirmed_by + confirmed_at
    """
    from api.models.booking import Booking
    from datetime import datetime

    role = current_user.get("role", "")
    if role == "TRAINER":
        raise HTTPException(status_code=403, detail="Forbidden")

    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status.upper() != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm booking with status '{booking.status}'",
        )

    try:
        sub_uuid = uuid.UUID(str(current_user.get("sub"))) if current_user.get("sub") else None
    except (ValueError, AttributeError):
        sub_uuid = None

    booking.status = "CONFIRMED"
    booking.confirmed_by = sub_uuid
    booking.confirmed_at = datetime.utcnow()
    db.flush()

    from api.services.activity_log import log as activity_log
    activity_log(db, current_user, "booking.confirm", "booking", str(booking_id))

    return booking_service._booking_to_dict(booking)


@router.post("/bookings/external", status_code=201)
def external_booking(
    body: ExternalBookingRequest,
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    External booking จาก customer product (API Key auth)
    Slots ต้องต่อเนื่องใน same day เท่านั้น
    """
    # ตรวจสอบ API key
    expected_key = getattr(settings, "EXTERNAL_BOOKING_API_KEY", None)
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    start_time_str = body.start_time
    end_time_str = body.end_time

    # Case 1: slot_times provided — validate contiguous, compute start/end
    if body.slot_times:
        times = sorted(body.slot_times)
        # Each slot is 1 hour — check contiguous
        for slot_index in range(1, len(times)):
            h_prev = int(times[slot_index - 1].split(":")[0])
            h_curr = int(times[slot_index].split(":")[0])
            if h_curr - h_prev != 1:
                raise HTTPException(status_code=400, detail="Slot times must be contiguous (1-hour intervals)")
        # Use date from start_time if provided, else today
        from datetime import date as date_type
        base_date = datetime.fromisoformat(body.start_time).date() if body.start_time else date_type.today()
        start_time_str = f"{base_date}T{times[0]}:00"
        end_time_str = f"{base_date}T{times[-1].split(':')[0].zfill(2)}:{times[-1].split(':')[1]}:00"
        # end_time = last slot + 1 hour
        last_h = int(times[-1].split(":")[0]) + 1
        end_time_str = f"{base_date}T{str(last_h).zfill(2)}:00:00"

    # Case 2: slots count provided — compute end_time from start_time + slots hours
    elif body.slots and body.start_time:
        start_dt = datetime.fromisoformat(body.start_time)
        end_dt = start_dt + timedelta(hours=body.slots)
        start_time_str = body.start_time
        end_time_str = end_dt.isoformat()

    # Validate we have both start and end
    if not start_time_str or not end_time_str:
        raise HTTPException(status_code=400, detail="Must provide start_time+end_time, start_time+slots, or slot_times")

    # Cross-day validation
    start_dt = datetime.fromisoformat(start_time_str)
    end_dt = datetime.fromisoformat(end_time_str)
    if start_dt.date() != end_dt.date():
        raise HTTPException(status_code=400, detail="Booking must be within the same day")

    payload = {
        "branch_id": body.branch_id,
        "customer_id": body.customer_id,
        "trainer_id": body.trainer_id,
        "start_time": start_time_str,
        "end_time": end_time_str,
        "notes": body.notes,
        "booking_type": "CUSTOMER",
        "booking_source": "EXTERNAL_API",
    }

    system_user = {"role": "EXTERNAL", "sub": None, "partner_id": None, "branch_id": None}
    return booking_service.create_booking(payload, system_user, db)
