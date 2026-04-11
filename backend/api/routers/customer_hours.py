"""
api/routers/customer_hours.py

Customer Hour endpoints:
  POST /customer-hours/deduct              — หักชั่วโมง (SELECT FOR UPDATE)
  PUT  /customer-hours/adjust              — ปรับยอดมือ (+ หรือ -)
  GET  /customer-hours/remaining/:id       — ยอดคงเหลือ
  GET  /customer-hours/log                 — ประวัติธุรกรรม
  GET  /customer-hours/trainer-report      — สรุปชั่วโมง trainer
"""
import uuid
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import customer_hours as hour_service

router = APIRouter()


class DeductRequest(BaseModel):
    customer_id: str
    trainer_id: Optional[str] = None
    branch_id: Optional[str] = None


class AdjustRequest(BaseModel):
    customer_id: str
    adjustment: float   # บวก = เพิ่ม, ลบ = หัก
    reason: Optional[str] = None


def _to_uuid(val) -> uuid.UUID | None:
    if not val:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


@router.post("/customer-hours/deduct")
def deduct_hours(
    body: DeductRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    หัก 1 ชั่วโมงจาก customer balance
    ใช้ SELECT FOR UPDATE ป้องกัน race condition (INT-06)
    คืน 400 ถ้า balance = 0
    """
    trainer_id = _to_uuid(body.trainer_id)
    branch_id = _to_uuid(body.branch_id) if body.branch_id else None
    return hour_service.deduct(_to_uuid(body.customer_id), trainer_id, branch_id, current_user, db)


@router.put("/customer-hours/adjust")
def adjust_hours(
    body: AdjustRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    ปรับยอดชั่วโมงมือ — admin+ เท่านั้น
    hours บวก = เพิ่ม, ลบ = หัก
    คืน 400 ถ้าจะทำให้ติดลบ
    """
    return hour_service.adjust(_to_uuid(body.customer_id), body.adjustment, body.reason, current_user, db)


@router.get("/customer-hours/remaining/{customer_id}")
def get_remaining(
    customer_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดูยอดคงเหลือชั่วโมงของลูกค้า"""
    return hour_service.get_remaining(customer_id, db)


@router.get("/customer-hours/log")
def list_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    customer_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดูประวัติธุรกรรมชั่วโมงทั้งหมด พร้อม filter"""
    return hour_service.list_log(
        current_user, db, page, page_size,
        customer_id, branch_id, start_date, end_date, transaction_type,
    )


@router.get("/customer-hours/trainer-report")
def trainer_report(
    trainer_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """สรุปชั่วโมงที่ trainer สอนไป"""
    return hour_service.trainer_report(
        current_user, db, trainer_id, branch_id, start_date, end_date,
    )


@router.get("/customer-hours/{customer_id}")
def get_customer_hours_legacy(
    customer_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """Legacy endpoint — เหมือน /customer-hours/remaining/:id"""
    return hour_service.get_remaining(customer_id, db)
