"""api/services/orders.py"""
import uuid
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.order import Order
from api.models.customer import Customer, CustomerHourBalance
from api.models.package import Package
from api.services.permissions import check_permission


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def _order_to_dict(order: Order) -> dict:
    return {
        "id": str(order.id),
        "partner_id": str(order.partner_id),
        "branch_id": str(order.branch_id),
        "customer_id": str(order.customer_id),
        "package_id": str(order.package_id) if order.package_id else None,
        "trainer_id": str(order.trainer_id) if order.trainer_id else None,
        "caretaker_id": str(order.caretaker_id) if order.caretaker_id else None,
        "order_date": str(order.order_date),
        "hours": order.hours,
        "bonus_hours": order.bonus_hours,
        "payment_method": order.payment_method,
        "total_price": float(order.total_price),
        "paid_amount": float(order.paid_amount),
        "is_renewal": order.is_renewal,
        "notes": order.notes,
        "created_at": str(order.created_at),
        "outstanding": float(order.total_price) - float(order.paid_amount),
        "has_outstanding": float(order.total_price) > float(order.paid_amount),
    }


def _apply_scope(query, current_user: dict):
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    branch_id = current_user.get("branch_id")
    if role == "DEVELOPER":
        pass
    elif role == "OWNER":
        query = query.filter(Order.partner_id == _to_uuid(partner_id))
    else:
        if branch_id:
            query = query.filter(Order.branch_id == _to_uuid(branch_id))
        else:
            query = query.filter(Order.partner_id == _to_uuid(partner_id))
    return query


def list_orders(current_user: dict, db: Session, page: int = 1, page_size: int = 20,
                customer_id: str = None) -> dict:
    query = db.query(Order)
    query = _apply_scope(query, current_user)
    if customer_id:
        query = query.filter(Order.customer_id == _to_uuid(customer_id))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_order_to_dict(order) for order in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_order(order_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_dict(order)


def create_order(payload: dict, current_user: dict, db: Session) -> dict:
    role = current_user.get("role", "").upper()

    # TRAINER cannot create orders
    if role == "TRAINER":
        raise HTTPException(status_code=403, detail="Forbidden")

    # Permission matrix check
    if not check_permission(db, role, "order", "CREATE"):
        raise HTTPException(status_code=403, detail="Forbidden")

    customer_id = _to_uuid(payload["customer_id"])
    customer = db.query(Customer).filter_by(id=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Package validation
    package_id = _to_uuid(payload.get("package_id"))
    if package_id:
        package = db.query(Package).filter_by(id=package_id).first()
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        if not package.is_active:
            raise HTTPException(status_code=400, detail="Package is not active")
        today = date.today()
        if package.active_from and package.active_from > today:
            raise HTTPException(status_code=400, detail="Package is not yet active")
        if package.active_until and package.active_until < today:
            raise HTTPException(status_code=400, detail="Package is no longer active")
        # Branch scope check
        order_branch_id = _to_uuid(payload.get("branch_id")) or customer.branch_id
        if package.branch_scope == "SPECIFIC" and package.branch_id and package.branch_id != order_branch_id:
            raise HTTPException(status_code=400, detail="Package not available for this branch")

    hours = payload.get("hours", 0)
    bonus_hours = payload.get("bonus_hours", 0)

    order = Order(
        partner_id=_to_uuid(current_user.get("partner_id")) or customer.partner_id,
        branch_id=_to_uuid(payload.get("branch_id")) or customer.branch_id,
        customer_id=customer_id,
        package_id=_to_uuid(payload.get("package_id")),
        trainer_id=_to_uuid(payload.get("trainer_id")),
        caretaker_id=_to_uuid(payload.get("caretaker_id")),
        order_date=date.fromisoformat(payload.get("order_date", str(date.today()))),
        hours=hours,
        bonus_hours=bonus_hours,
        payment_method=payload.get("payment_method", "BANK_TRANSFER"),
        total_price=payload.get("total_price", 0),
        paid_amount=payload.get("paid_amount", payload.get("total_price", 0)),
        price_per_session=payload.get("price_per_session"),
        is_renewal=payload.get("is_renewal", False),
        notes=payload.get("notes"),
    )
    db.add(order)
    db.flush()

    # Allocate hours to customer balance
    balance = db.query(CustomerHourBalance).filter_by(customer_id=customer_id).with_for_update().first()
    if balance:
        balance.remaining = float(balance.remaining) + hours + bonus_hours
    else:
        db.add(CustomerHourBalance(customer_id=customer_id, remaining=hours + bonus_hours))
    db.flush()

    _log(db, current_user, "order.create", str(order.id))
    return _order_to_dict(order)


def update_order(order_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    for field in ["payment_method", "paid_amount", "notes"]:
        if field in payload:
            setattr(order, field, payload[field])
    db.flush()
    _log(db, current_user, "order.edit", str(order_id))
    return _order_to_dict(order)


def delete_order(order_id: uuid.UUID, current_user: dict, db: Session) -> None:
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.flush()
    _log(db, current_user, "order.delete", str(order_id))


def _log(db, current_user, action, target_id):
    """Helper สำหรับ activity log — delegate ไปที่ activity_log service"""
    from api.services.activity_log import log as activity_log
    activity_log(db, current_user, action, "order", target_id)
