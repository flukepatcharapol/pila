"""
api/services/dashboard.py

Business logic สำหรับ Dashboard — aggregate data ตาม role
แต่ละ role เห็น card ต่างกัน:
  trainer      → hours trained today/MTD, customer count, bookings
  admin        → orders today, hours deducted today
  branch_master → total orders, revenue, breakdown by admin + trainer
  owner        → branch_master view + all branches
  developer    → owner view + partner selector
"""
import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.models.customer import Customer
from api.models.order import Order
from api.models.booking import Booking
from api.models.customer_hour import CustomerHourLog
from api.models.user import User
from api.models.trainer import Trainer


def _to_uuid(val) -> uuid.UUID | None:
    if not val:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def get_dashboard(current_user: dict, db: Session,
                  range_type: str = "today",
                  start_date: str = None, end_date: str = None,
                  branch_id: uuid.UUID = None) -> dict:
    """
    ดึง dashboard data ตาม role + time range
    range_type: today|week|month|custom
    """
    role = current_user.get("role", "")
    user_branch_id = _to_uuid(current_user.get("branch_id"))
    partner_id = _to_uuid(current_user.get("partner_id"))

    # คำนวณ date range
    start_dt, end_dt = _resolve_date_range(range_type, start_date, end_date)

    # กำหนด branch scope สำหรับ query
    # branch_id param override ใน owner+ เท่านั้น
    effective_branch_id = None
    if role in ("ADMIN", "TRAINER", "BRANCH_MASTER"):
        effective_branch_id = user_branch_id
    elif role in ("OWNER", "DEVELOPER") and branch_id:
        effective_branch_id = branch_id

    # คำนวณ metrics พื้นฐาน
    customer_q = db.query(Customer)
    order_q = db.query(Order)
    booking_q = db.query(Booking)
    deduct_q = db.query(CustomerHourLog).filter(
        CustomerHourLog.transaction_type == "HOUR_DEDUCT",
        CustomerHourLog.created_at >= start_dt,
        CustomerHourLog.created_at <= end_dt,
    )

    # Apply scope
    if effective_branch_id:
        customer_q = customer_q.filter(Customer.branch_id == effective_branch_id)
        order_q = order_q.filter(Order.branch_id == effective_branch_id)
        booking_q = booking_q.filter(Booking.branch_id == effective_branch_id)
        deduct_q = deduct_q.filter(CustomerHourLog.branch_id == effective_branch_id)
    elif role == "OWNER" and partner_id:
        # owner เห็นทุก branch ใน partner — filter ด้วย partner_id
        customer_q = customer_q.filter(Customer.partner_id == partner_id)
        order_q = order_q.filter(Order.partner_id == partner_id)

    # Orders ใน date range
    order_q_period = order_q.filter(
        Order.order_date >= start_dt.date(),
        Order.order_date <= end_dt.date(),
    )

    total_customers = customer_q.count()
    total_orders = order_q_period.count()

    # Revenue = sum ของ total_price ใน period
    revenue_result = order_q_period.with_entities(func.coalesce(func.sum(Order.total_price), 0)).scalar()
    total_revenue = float(revenue_result or 0)

    # Hours deducted ใน period
    hours_result = deduct_q.with_entities(func.coalesce(func.sum(func.abs(CustomerHourLog.amount)), 0)).scalar()
    total_hours_deducted = float(hours_result or 0)

    # Bookings ใน period
    booking_q_period = booking_q.filter(
        Booking.start_time >= start_dt,
        Booking.start_time <= end_dt,
    )
    total_bookings = booking_q_period.count()

    result = {
        "role": role,
        "range": range_type,
        "start_date": str(start_dt.date()),
        "end_date": str(end_dt.date()),
        "total_customers": total_customers,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_hours_deducted": total_hours_deducted,
        "total_bookings": total_bookings,
    }

    # branch_master+ เพิ่ม outstanding + breakdowns
    if role in ("BRANCH_MASTER", "OWNER", "DEVELOPER"):
        outstanding_result = order_q.with_entities(
            func.coalesce(func.sum(Order.total_price - Order.paid_amount), 0)
        ).scalar()
        result["total_outstanding"] = float(outstanding_result or 0)

        # breakdown_by_admin: group orders by created_by user
        admin_rows = (
            order_q_period
            .filter(Order.created_by.isnot(None))
            .with_entities(Order.created_by, func.count(Order.id), func.sum(Order.total_price))
            .group_by(Order.created_by)
            .all()
        )
        result["breakdown_by_admin"] = [
            {
                "user_id": str(row[0]),
                "order_count": int(row[1]),
                "total_revenue": float(row[2] or 0),
            }
            for row in admin_rows
        ]

        # breakdown_by_trainer: group deductions by trainer_id
        trainer_rows = (
            deduct_q
            .filter(CustomerHourLog.trainer_id.isnot(None))
            .with_entities(CustomerHourLog.trainer_id, func.count(CustomerHourLog.id), func.sum(func.abs(CustomerHourLog.amount)))
            .group_by(CustomerHourLog.trainer_id)
            .all()
        )
        result["breakdown_by_trainer"] = [
            {
                "trainer_id": str(row[0]),
                "session_count": int(row[1]),
                "total_hours": float(row[2] or 0),
            }
            for row in trainer_rows
        ]

    # trainer gets their own session stats
    if role == "TRAINER":
        result["total_hours"] = total_hours_deducted
        result["session_count"] = total_bookings

    return result


def _resolve_date_range(range_type: str, start_date: str, end_date: str):
    """แปลง range_type → (start_datetime, end_datetime)"""
    today = date.today()

    if range_type == "today":
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    elif range_type == "week":
        # Monday of current week
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    elif range_type == "month":
        start = datetime.combine(today.replace(day=1), datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    elif range_type == "custom" and start_date and end_date:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date + "T23:59:59")
    else:
        # default: today
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())

    return start, end
