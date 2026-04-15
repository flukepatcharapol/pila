"""
api/services/packages.py

Business logic สำหรับ Package CRUD + branch scope management
"""
import uuid
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.package import Package, PackageBranchScope
from api.models.order import Order
from api.services.activity_log import log as activity_log

MAX_PAGE_SIZE = 100


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def _to_dict(package: Package, db: Session = None) -> dict:
    """แปลง Package → dict พร้อม branch_ids ถ้า branch_scope = SELECTED"""
    package_dict = {
        "id": str(package.id),
        "partner_id": str(package.partner_id),
        "name": package.name,
        "hours": float(package.hours),
        "sale_type": package.sale_type,
        "price": float(package.price),
        "branch_scope": package.branch_scope,
        "is_active": package.is_active,
        "active_from": str(package.active_from) if package.active_from else None,
        "active_until": str(package.active_until) if package.active_until else None,
    }
    # ถ้า branch_scope = SELECTED ดึง branch_ids มาด้วย
    if db and package.branch_scope == "SELECTED":
        scopes = db.query(PackageBranchScope).filter_by(package_id=package.id).all()
        package_dict["branch_ids"] = [str(scope.branch_id) for scope in scopes]
    return package_dict


def _is_available(package: Package) -> bool:
    """
    ตรวจสอบว่า package พร้อมใช้งานใน order form:
    - is_active ต้อง True
    - sale_type ต้องไม่ใช่ PRE_SALE
    - active_from/until ต้องอยู่ในช่วงเวลา (ถ้ากำหนด)
    """
    if not package.is_active:
        return False
    if package.sale_type == "PRE_SALE":
        return False
    today = date.today()
    if package.active_from and today < package.active_from:
        return False
    if package.active_until and today > package.active_until:
        return False
    return True


def list_packages(current_user: dict, db: Session, page: int = 1, page_size: int = 20,
                  active_only: bool = False, branch_id: str = None) -> dict:
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size cannot exceed {MAX_PAGE_SIZE}")

    query = db.query(Package)
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")

    # DEVELOPER เห็นทั้งหมด ส่วน role อื่นเห็นแค่ partner ตัวเอง
    if role != "DEVELOPER" and partner_id:
        query = query.filter(Package.partner_id == _to_uuid(partner_id))

    if active_only:
        # กรองเฉพาะ package ที่พร้อมใช้งาน (active + ไม่ใช่ pre-sale + อยู่ในช่วงเวลา)
        query = query.filter(Package.is_active == True, Package.sale_type == "SALE")
        today = date.today()
        query = query.filter(
            (Package.active_from == None) | (Package.active_from <= today)
        ).filter(
            (Package.active_until == None) | (Package.active_until >= today)
        )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for package in items:
        package_dict = _to_dict(package, db)
        # เพิ่ม status badge: Active / Inactive / Expired / Pre-sale
        package_dict["status"] = _get_display_status(package).lower()
        # เพิ่ม is_available สำหรับ order form
        package_dict["is_available"] = _is_available(package)
        result.append(package_dict)

    return {"items": result, "total": total, "page": page, "page_size": page_size}


def _get_display_status(package: Package) -> str:
    """คำนวณ status badge สำหรับแสดงใน UI"""
    if not package.is_active:
        return "INACTIVE"
    today = date.today()
    if package.active_until and today > package.active_until:
        return "EXPIRED"
    if package.sale_type == "PRE_SALE":
        return "PRE_SALE"
    return "ACTIVE"


def get_package(package_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    package = db.query(Package).filter_by(id=package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    package_dict = _to_dict(package, db)
    package_dict["status"] = _get_display_status(package).lower()
    package_dict["is_available"] = _is_available(package)
    return package_dict


def create_package(payload: dict, current_user: dict, db: Session) -> dict:
    partner_id = _to_uuid(current_user.get("partner_id"))
    package = Package(
        partner_id=partner_id,
        name=payload["name"],
        hours=payload["hours"],
        sale_type=payload.get("sale_type", "SALE"),
        price=payload["price"],
        branch_scope=payload.get("branch_scope", "ALL"),
        is_active=payload.get("is_active", True),
        active_from=date.fromisoformat(payload["active_from"]) if payload.get("active_from") else None,
        active_until=date.fromisoformat(payload["active_until"]) if payload.get("active_until") else None,
    )
    db.add(package)
    db.flush()

    # ถ้า branch_scope = SELECTED ให้บันทึก branch_ids ลง package_branch_scopes
    if package.branch_scope == "SELECTED" and payload.get("branch_ids"):
        for bid in payload["branch_ids"]:
            db.add(PackageBranchScope(package_id=package.id, branch_id=_to_uuid(bid)))
        db.flush()

    activity_log(db, current_user, "package.create", "package", str(package.id),
                 detail=f"Created package: {payload['name']}")
    return _to_dict(package, db)


def update_package(package_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    package = db.query(Package).filter_by(id=package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    before = _to_dict(package)
    for field in ["name", "price", "is_active", "sale_type", "branch_scope"]:
        if field in payload and payload[field] is not None:
            setattr(package, field, payload[field])
    if "active_from" in payload:
        package.active_from = date.fromisoformat(payload["active_from"]) if payload["active_from"] else None
    if "active_until" in payload:
        package.active_until = date.fromisoformat(payload["active_until"]) if payload["active_until"] else None

    # อัปเดต branch scopes ถ้ามี
    if "branch_ids" in payload:
        db.query(PackageBranchScope).filter_by(package_id=package_id).delete()
        if package.branch_scope == "SELECTED" and payload["branch_ids"]:
            for bid in payload["branch_ids"]:
                db.add(PackageBranchScope(package_id=package.id, branch_id=_to_uuid(bid)))
    db.flush()

    activity_log(db, current_user, "package.edit", "package", str(package_id),
                 changes={"before": before, "after": _to_dict(package)})
    return _to_dict(package, db)


def delete_package(package_id: uuid.UUID, current_user: dict, db: Session) -> None:
    package = db.query(Package).filter_by(id=package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # INT-05: ไม่ลบ package ที่อยู่ใน order อยู่แล้ว
    in_orders = db.query(Order).filter_by(package_id=package_id).count()
    if in_orders > 0:
        raise HTTPException(
            status_code=409,
            detail="Package referenced by existing orders",
        )

    db.delete(package)
    db.flush()
    activity_log(db, current_user, "package.delete", "package", str(package_id))
