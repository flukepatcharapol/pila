"""
api/services/customers.py

Business logic สำหรับ Customer CRUD
"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.models.customer import Customer, CustomerHourBalance, CustomerCodeCounter
from api.models.trainer import Trainer, Caretaker
from api.models.order import Order
from api.services.customer import generate_customer_code


MAX_PAGE_SIZE = 100


def _to_uuid(val) -> uuid.UUID | None:
    if not val:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _apply_branch_filter(query, current_user: dict, db: Session):
    """Apply branch/partner filter ตาม role"""
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    branch_id = current_user.get("branch_id")

    if role == "DEVELOPER":
        pass  # เห็นทุกอย่าง
    elif role in ("OWNER",):
        query = query.filter(Customer.partner_id == _to_uuid(partner_id))
    else:
        # BRANCH_MASTER, ADMIN, TRAINER — เห็นแค่ branch ตัวเอง
        if branch_id:
            query = query.filter(Customer.branch_id == _to_uuid(branch_id))
        else:
            query = query.filter(Customer.partner_id == _to_uuid(partner_id))

    return query


def list_customers(
    current_user: dict,
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    status: str = None,
    branch: str = None,
) -> dict:
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"page_size cannot exceed {MAX_PAGE_SIZE}",
        )

    query = db.query(Customer)
    query = _apply_branch_filter(query, current_user, db)

    if search:
        query = query.filter(
            (Customer.first_name.ilike(f"%{search}%")) |
            (Customer.last_name.ilike(f"%{search}%")) |
            (Customer.nickname.ilike(f"%{search}%")) |
            (Customer.customer_code.ilike(f"%{search}%"))
        )

    if status:
        query = query.filter(Customer.status.ilike(status))

    if branch:
        from api.models.branch import Branch
        branch_obj = db.query(Branch).filter(Branch.name.ilike(branch)).first()
        if branch_obj:
            query = query.filter(Customer.branch_id == branch_obj.id)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return {
        "items": [_customer_to_dict(c, db) for c in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_customer(customer_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    customer = db.query(Customer).filter_by(id=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Branch access check
    _check_access(customer, current_user)

    # Eager load related data
    hour_balance = db.query(CustomerHourBalance).filter_by(customer_id=customer.id).first()
    orders = db.query(Order).filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).all()

    data = _customer_to_dict(customer, db)
    data["remaining_hours"] = float(hour_balance.remaining) if hour_balance else 0.0
    data["order_history"] = [
        {
            "id": str(o.id),
            "order_date": str(o.order_date),
            "hours": o.hours,
            "bonus_hours": o.bonus_hours,
            "total_price": float(o.total_price),
            "payment_method": o.payment_method,
        }
        for o in orders
    ]
    return data


def create_customer(payload: dict, current_user: dict, db: Session) -> dict:
    branch_id = _to_uuid(payload["branch_id"])
    source_type_id = _to_uuid(payload["source_type_id"])
    trainer_id = _to_uuid(payload.get("trainer_id"))
    caretaker_id = _to_uuid(payload.get("caretaker_id"))

    # Validate trainer belongs to branch
    if trainer_id:
        trainer = db.query(Trainer).filter_by(id=trainer_id).first()
        if not trainer or trainer.branch_id != branch_id:
            raise HTTPException(
                status_code=400,
                detail="Trainer does not belong to selected branch",
            )

    # Validate caretaker belongs to branch
    if caretaker_id:
        caretaker = db.query(Caretaker).filter_by(id=caretaker_id).first()
        if not caretaker or caretaker.branch_id != branch_id:
            raise HTTPException(
                status_code=400,
                detail="Caretaker does not belong to selected branch",
            )

    # Get branch prefix for code generation
    from api.models.branch import Branch
    from api.models.user import SourceType
    branch = db.query(Branch).filter_by(id=branch_id).first()
    source_type = db.query(SourceType).filter_by(id=source_type_id).first()

    if not branch or not source_type:
        raise HTTPException(status_code=400, detail="Invalid branch or source type")

    customer_code = generate_customer_code(
        branch_prefix=branch.prefix,
        source_code=source_type.code,
        db=db,
    )

    partner_id = _to_uuid(current_user.get("partner_id")) or branch.partner_id

    # auto-suggest display_name จาก nickname ถ้าไม่ระบุ
    nickname = payload.get("nickname")
    display_name = payload.get("display_name") or nickname

    customer = Customer(
        partner_id=partner_id,
        branch_id=branch_id,
        source_type_id=source_type_id,
        customer_code=customer_code,
        first_name=payload["first_name"],
        last_name=payload.get("last_name"),
        nickname=nickname,
        display_name=display_name,
        contact_channel=payload.get("contact_channel"),
        phone=payload.get("phone"),
        email=payload.get("email"),
        line_id=payload.get("line_id"),
        birthday=payload.get("birthday"),
        notes=payload.get("notes"),
        profile_photo_url=payload.get("profile_photo_url"),
        is_duplicate=payload.get("is_duplicate", False),
        status=payload.get("status", "ACTIVE"),
        trainer_id=trainer_id,
        caretaker_id=caretaker_id,
        created_by=_to_uuid(current_user.get("sub")),
    )
    db.add(customer)
    db.flush()

    db.add(CustomerHourBalance(customer_id=customer.id, remaining=0))
    db.flush()

    _log_activity(db, current_user, "customer.create", str(customer.id))

    return _customer_to_dict(customer, db)


def update_customer(customer_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    customer = db.query(Customer).filter_by(id=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    _check_access(customer, current_user)

    updatable = [
        "first_name", "last_name", "nickname", "display_name", "contact_channel",
        "phone", "email", "line_id", "birthday", "notes", "profile_photo_url",
        "is_duplicate", "status", "trainer_id", "caretaker_id",
    ]
    for field in updatable:
        if field in payload and payload[field] is not None:
            setattr(customer, field, payload[field])

    db.flush()
    _log_activity(db, current_user, "customer.edit", str(customer.id))
    return _customer_to_dict(customer, db)


def delete_customer(customer_id: uuid.UUID, current_user: dict, db: Session) -> None:
    customer = db.query(Customer).filter_by(id=customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    _check_access(customer, current_user)
    _check_delete_permission(current_user, db)

    # Cascade delete dependent records to avoid FK violations
    db.query(CustomerHourBalance).filter_by(customer_id=customer_id).delete()
    db.flush()

    db.delete(customer)
    db.flush()
    _log_activity(db, current_user, "customer.delete", str(customer_id))


def _check_access(customer: Customer, current_user: dict):
    role = current_user.get("role", "")
    if role == "DEVELOPER":
        return
    partner_id = _to_uuid(current_user.get("partner_id"))
    branch_id = _to_uuid(current_user.get("branch_id"))
    if partner_id and customer.partner_id != partner_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if role not in ("OWNER",) and branch_id and customer.branch_id != branch_id:
        raise HTTPException(status_code=403, detail="Access denied")


def _check_delete_permission(current_user: dict, db: Session):
    role = current_user.get("role", "")
    if role in ("OWNER", "BRANCH_MASTER", "DEVELOPER"):
        return

    if role == "ADMIN":
        # ตรวจ permission matrix
        from api.models.permission import PermissionMatrix
        perm = db.query(PermissionMatrix).filter_by(
            role="admin", feature_name="customer", action="delete"
        ).first()
        if perm and not perm.is_allowed:
            raise HTTPException(status_code=403, detail="Permission denied")
        return

    raise HTTPException(status_code=403, detail="Permission denied")


def _customer_to_dict(customer: Customer, db: Session) -> dict:
    trainer_name = None
    caretaker_name = None
    if customer.trainer_id:
        t = db.query(Trainer).filter_by(id=customer.trainer_id).first()
        trainer_name = t.name if t else None
    if customer.caretaker_id:
        c = db.query(Caretaker).filter_by(id=customer.caretaker_id).first()
        caretaker_name = c.name if c else None

    return {
        "id": str(customer.id),
        "customer_code": customer.customer_code,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "nickname": customer.nickname,
        "display_name": customer.display_name,
        "contact_channel": customer.contact_channel,
        "phone": customer.phone,
        "email": customer.email,
        "line_id": customer.line_id,
        "birthday": str(customer.birthday) if customer.birthday else None,
        "notes": customer.notes,
        "profile_photo_url": customer.profile_photo_url,
        "is_duplicate": customer.is_duplicate,
        "status": customer.status,
        "branch_id": str(customer.branch_id),
        "partner_id": str(customer.partner_id),
        "source_type_id": str(customer.source_type_id) if customer.source_type_id else None,
        "trainer_id": str(customer.trainer_id) if customer.trainer_id else None,
        "caretaker_id": str(customer.caretaker_id) if customer.caretaker_id else None,
        "trainer_name": trainer_name,
        "caretaker_name": caretaker_name,
        "created_at": str(customer.created_at),
    }


def _log_activity(db: Session, current_user: dict, action: str, target_id: str):
    from api.models.activity_log import ActivityLog
    db.add(ActivityLog(
        user_id=_to_uuid(current_user.get("sub")),
        partner_id=_to_uuid(current_user.get("partner_id")),
        branch_id=_to_uuid(current_user.get("branch_id")),
        action=action,
        target_id=target_id,
        target_type="customer",
    ))
    db.flush()
