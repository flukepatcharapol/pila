"""api/routers/integrity.py — Data integrity check endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.models.customer import Customer, CustomerHourBalance

router = APIRouter()


@router.get("/integrity/customer-hours")
def check_customer_hours_integrity(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ตรวจสอบว่าทุก customer มี hour_balance record"""
    customers_without_balance = (
        db.query(Customer)
        .filter(~Customer.id.in_(
            db.query(CustomerHourBalance.customer_id)
        ))
        .count()
    )
    return {
        "check": "customer_hours",
        "status": "ok" if customers_without_balance == 0 else "issues_found",
        "customers_without_balance": customers_without_balance,
    }


@router.get("/integrity/orphaned-orders")
def check_orphaned_orders(current_user: dict = Depends(require_pin_verified), db: Session = Depends(get_db)):
    from api.models.order import Order
    orphaned = db.query(Order).filter(
        ~Order.customer_id.in_(db.query(Customer.id))
    ).count()
    return {"check": "orphaned_orders", "status": "ok" if orphaned == 0 else "issues_found", "count": orphaned}


@router.post("/integrity/fix-customer-hours")
def fix_missing_customer_hour_balances(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    customers_without_balance = (
        db.query(Customer)
        .filter(~Customer.id.in_(db.query(CustomerHourBalance.customer_id)))
        .all()
    )
    fixed = 0
    for customer in customers_without_balance:
        db.add(CustomerHourBalance(customer_id=customer.id, remaining=0))
        fixed += 1
    db.flush()
    return {"fixed": fixed}
