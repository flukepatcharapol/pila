"""
api/routers/orders.py

Order endpoints:
  GET    /orders
  POST   /orders
  GET    /orders/:id
  PUT    /orders/:id
  DELETE /orders/:id
  POST   /orders/:id/payments    — บันทึก installment payment
  GET    /orders/:id/payments    — ดูประวัติการชำระ
  POST   /orders/:id/receipt     — resend receipt email
"""
import uuid
from uuid import UUID
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import orders as order_service
from api.models.order import OrderPayment
from api.services.activity_log import log as activity_log

router = APIRouter()


class CreateOrderRequest(BaseModel):
    customer_id: str
    package_id: Optional[str] = None
    branch_id: Optional[str] = None
    order_date: Optional[str] = None
    hours: int = Field(default=0, ge=0)
    bonus_hours: int = Field(default=0, ge=0)
    payment_method: str = "BANK_TRANSFER"
    total_price: float = Field(ge=0)
    paid_amount: Optional[float] = Field(default=None, ge=0)
    price_per_session: Optional[float] = None
    trainer_id: Optional[str] = None
    caretaker_id: Optional[str] = None
    is_renewal: bool = False
    notes: Optional[str] = None


class UpdateOrderRequest(BaseModel):
    payment_method: Optional[str] = None
    paid_amount: Optional[float] = None
    notes: Optional[str] = None


class RecordPaymentRequest(BaseModel):
    amount: float
    paid_at: Optional[str] = None   # ISO date string, default today
    note: Optional[str] = None


@router.get("/orders")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    customer_id: Optional[str] = Query(None),
    has_outstanding: Optional[bool] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return order_service.list_orders(current_user, db, page, page_size, customer_id)


@router.post("/orders", status_code=201)
def create_order(
    body: CreateOrderRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return order_service.create_order(body.model_dump(), current_user, db)


@router.get("/orders/{order_id}")
def get_order(
    order_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return order_service.get_order(order_id, current_user, db)


@router.put("/orders/{order_id}")
def update_order(
    order_id: UUID,
    body: UpdateOrderRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return order_service.update_order(order_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/orders/{order_id}", status_code=204)
def delete_order(
    order_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    order_service.delete_order(order_id, current_user, db)


@router.post("/orders/{order_id}/payments", status_code=201)
def record_payment(
    order_id: UUID,
    body: RecordPaymentRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    บันทึก installment payment สำหรับ order
    อัปเดต paid_amount ใน orders ด้วย
    """
    from api.models.order import Order
    from fastapi import HTTPException

    order = db.query(Order).filter_by(id=order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    paid_at = date.fromisoformat(body.paid_at) if body.paid_at else date.today()

    try:
        recorded_by = uuid.UUID(str(current_user.get("sub"))) if current_user.get("sub") else None
    except (ValueError, AttributeError):
        recorded_by = None

    # บันทึก payment record
    payment = OrderPayment(
        order_id=order_id,
        amount=body.amount,
        paid_at=paid_at,
        note=body.note,
        recorded_by=recorded_by,
    )
    db.add(payment)

    # อัปเดต paid_amount ใน order
    order.paid_amount = float(order.paid_amount) + body.amount
    db.flush()

    activity_log(db, current_user, "order.payment", "order", str(order_id),
                 detail=f"Recorded payment: {body.amount}")

    return {
        "id": str(payment.id),
        "order_id": str(order_id),
        "amount": body.amount,
        "paid_at": str(paid_at),
        "note": body.note,
        "new_paid_amount": float(order.paid_amount),
        "outstanding": float(order.total_price) - float(order.paid_amount),
    }


@router.get("/orders/{order_id}/payments")
def list_payments(
    order_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดูประวัติการชำระเงินทั้งหมดของ order"""
    payments = db.query(OrderPayment).filter_by(order_id=order_id).order_by(OrderPayment.created_at.desc()).all()
    return [
        {
            "id": str(payment.id),
            "amount": float(payment.amount),
            "paid_at": str(payment.paid_at),
            "note": payment.note,
            "recorded_by": str(payment.recorded_by) if payment.recorded_by else None,
            "created_at": str(payment.created_at),
        }
        for payment in payments
    ]


@router.post("/orders/{order_id}/receipt")
def resend_receipt(
    order_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """Resend receipt email — ใน test env แค่ return success"""
    from api.models.order import Order
    from fastapi import HTTPException

    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # TODO: ส่ง email จริงผ่าน Celery task ใน production
    return {"message": "Receipt sent", "order_id": str(order_id)}
