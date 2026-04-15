"""
api/services/customer_hours.py

Business logic สำหรับ Customer Hour:
  - deduct: หักชั่วโมง 1 ครั้ง (ใช้ SELECT FOR UPDATE ป้องกัน race condition)
  - adjust: ปรับยอดมือ (+ หรือ -)
  - get_remaining: ดูยอดคงเหลือ
  - list_log: ดูประวัติธุรกรรม
  - trainer_report: สรุปชั่วโมง trainer
"""
import uuid
from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.customer import Customer, CustomerHourBalance
from api.models.customer_hour import CustomerHourLog
from api.services.activity_log import log as activity_log

# จำนวนชั่วโมงที่หักต่อครั้ง (1 deduction = 1 ชั่วโมง)
DEDUCT_AMOUNT = 1

MAX_PAGE_SIZE = 100


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def deduct(customer_id: uuid.UUID, trainer_id: uuid.UUID | None, branch_id: uuid.UUID | None, current_user: dict, db: Session) -> dict:
    """
    หักชั่วโมง 1 ครั้งจาก customer balance

    ใช้ SELECT FOR UPDATE เพื่อป้องกัน race condition:
    ถ้ามี 2 request deduct พร้อมกัน row lock จะบังคับให้รัน sequential
    หยุด double-deduction
    """
    # ล็อก row เพื่อ prevent concurrent deduction (INT-06)
    balance = (
        db.query(CustomerHourBalance)
        .filter_by(customer_id=customer_id)
        .with_for_update()  # SELECT FOR UPDATE — row lock
        .first()
    )

    if not balance:
        raise HTTPException(status_code=404, detail="Customer hour balance not found")

    before = float(balance.remaining)

    # ตรวจสอบ zero balance — ไม่อนุญาตหักจาก 0
    if before <= 0:
        raise HTTPException(
            status_code=400,
            detail="Insufficient hours: customer has no remaining hours",
        )

    # คำนวณยอดใหม่ (ป้องกัน negative ด้วย max)
    after = max(0.0, before - DEDUCT_AMOUNT)
    balance.remaining = after

    branch_id = branch_id or _to_uuid(current_user.get("branch_id"))
    user_id = _to_uuid(current_user.get("sub"))

    # บันทึก log ธุรกรรม
    db.add(CustomerHourLog(
        customer_id=customer_id,
        branch_id=branch_id,
        trainer_id=trainer_id,
        transaction_type="HOUR_DEDUCT",
        before_amount=int(before),
        amount=-DEDUCT_AMOUNT,
        after_amount=int(after),
        user_id=user_id,
    ))
    db.flush()

    activity_log(
        db, current_user, "customer_hour.deduct", "customer", str(customer_id),
        detail=f"Deducted {DEDUCT_AMOUNT}h: {before} → {after}",
    )

    return {
        "customer_id": str(customer_id),
        "before": before,
        "deducted": DEDUCT_AMOUNT,
        "remaining": after,
    }


def adjust(customer_id: uuid.UUID, adjustment: float, reason: str | None, current_user: dict, db: Session) -> dict:
    """
    ปรับยอดชั่วโมงมือ — admin เท่านั้น
    hours: บวก=เพิ่ม, ลบ=หัก
    ไม่อนุญาตให้ยอดต่ำกว่า 0
    """
    balance = (
        db.query(CustomerHourBalance)
        .filter_by(customer_id=customer_id)
        .with_for_update()
        .first()
    )

    if not balance:
        raise HTTPException(status_code=404, detail="Customer not found")

    before = float(balance.remaining)
    after = before + adjustment

    # INT-01: session balance ห้ามติดลบ
    if after < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Adjustment would result in negative balance ({after:.1f})",
        )

    balance.remaining = after

    user_id = _to_uuid(current_user.get("sub"))

    db.add(CustomerHourLog(
        customer_id=customer_id,
        transaction_type="HOUR_ADJUST",
        before_amount=int(before),
        amount=int(adjustment),
        after_amount=int(after),
        reason=reason,
        user_id=user_id,
    ))
    db.flush()

    activity_log(
        db, current_user, "customer_hour.adjust", "customer", str(customer_id),
        detail=f"Adjusted {adjustment:+.1f}h: {before} → {after}. Reason: {reason}",
    )

    return {
        "customer_id": str(customer_id),
        "before": before,
        "adjusted": adjustment,
        "remaining": after,
        "reason": reason,
    }


def get_remaining(customer_id: uuid.UUID, db: Session) -> dict:
    """ดูยอดคงเหลือ — ไม่ต้อง lock เพราะเป็น read-only"""
    balance = db.query(CustomerHourBalance).filter_by(customer_id=customer_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": str(customer_id), "hour_balance": float(balance.remaining)}


def list_log(current_user: dict, db: Session, page: int = 1, page_size: int = 20,
             customer_id: uuid.UUID = None, branch_id: uuid.UUID = None,
             start_date: str = None, end_date: str = None,
             transaction_type: str = None) -> dict:
    """ดูประวัติธุรกรรมชั่วโมง พร้อม filter"""
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size cannot exceed {MAX_PAGE_SIZE}")

    query = db.query(CustomerHourLog)

    # scope filter ตาม role
    role = current_user.get("role", "")
    user_branch_id = _to_uuid(current_user.get("branch_id"))
    if role not in ("DEVELOPER", "OWNER") and user_branch_id:
        query = query.filter(CustomerHourLog.branch_id == user_branch_id)

    if customer_id:
        query = query.filter(CustomerHourLog.customer_id == customer_id)
    if branch_id:
        query = query.filter(CustomerHourLog.branch_id == branch_id)
    if transaction_type:
        query = query.filter(CustomerHourLog.transaction_type == transaction_type.upper())
    if start_date:
        query = query.filter(CustomerHourLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(CustomerHourLog.created_at <= datetime.fromisoformat(end_date + "T23:59:59"))

    total = query.count()
    items = query.order_by(CustomerHourLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": str(log.id),
                "customer_id": str(log.customer_id),
                "branch_id": str(log.branch_id) if log.branch_id else None,
                "trainer_id": str(log.trainer_id) if log.trainer_id else None,
                "transaction_type": log.transaction_type,
                "before": log.before_amount,
                "amount": log.amount,
                "after": log.after_amount,
                "reason": log.reason,
                "user_id": str(log.user_id) if log.user_id else None,
                "created_at": str(log.created_at),
            }
            for log in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def trainer_report(current_user: dict, db: Session,
                   trainer_id: uuid.UUID = None, branch_id: uuid.UUID = None,
                   start_date: str = None, end_date: str = None) -> dict:
    """สรุปชั่วโมงของ trainer — นับจาก HOUR_DEDUCT logs"""
    role = current_user.get("role", "").upper()

    # TRAINER cannot view specific trainer_id report (could be another trainer)
    if role == "TRAINER" and trainer_id is not None:
        raise HTTPException(status_code=403, detail="Forbidden")

    query = db.query(CustomerHourLog).filter(
        CustomerHourLog.transaction_type == "HOUR_DEDUCT"
    )
    user_branch_id = _to_uuid(current_user.get("branch_id"))
    if role not in ("DEVELOPER", "OWNER") and user_branch_id:
        query = query.filter(CustomerHourLog.branch_id == user_branch_id)

    if trainer_id:
        query = query.filter(CustomerHourLog.trainer_id == trainer_id)
    if branch_id:
        query = query.filter(CustomerHourLog.branch_id == branch_id)
    if start_date:
        query = query.filter(CustomerHourLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(CustomerHourLog.created_at <= datetime.fromisoformat(end_date + "T23:59:59"))

    logs = query.order_by(CustomerHourLog.created_at.desc()).all()

    # คำนวณ total hours (abs เพราะ amount เป็นลบ)
    total_hours = sum(abs(log.amount) for log in logs)

    return {
        "total_hours": total_hours,
        "session_count": len(logs),
        "history": [
            {
                "id": str(log.id),
                "customer_id": str(log.customer_id),
                "trainer_id": str(log.trainer_id) if log.trainer_id else None,
                "hours": abs(log.amount),
                "created_at": str(log.created_at),
            }
            for log in logs
        ],
    }
