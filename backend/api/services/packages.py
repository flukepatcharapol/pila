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


def _to_uuid(val) -> uuid.UUID | None:
    if not val:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _to_dict(p: Package, db: Session = None) -> dict:
    """แปลง Package → dict พร้อม branch_ids ถ้า branch_scope = SELECTED"""
    d = {
        "id": str(p.id),
        "partner_id": str(p.partner_id),
        "name": p.name,
        "hours": float(p.hours),
        "sale_type": p.sale_type,
        "price": float(p.price),
        "branch_scope": p.branch_scope,
        "is_active": p.is_active,
        "active_from": str(p.active_from) if p.active_from else None,
        "active_until": str(p.active_until) if p.active_until else None,
    }
    # ถ้า branch_scope = SELECTED ดึง branch_ids มาด้วย
    if db and p.branch_scope == "SELECTED":
        scopes = db.query(PackageBranchScope).filter_by(package_id=p.id).all()
        d["branch_ids"] = [str(s.branch_id) for s in scopes]
    return d


def _is_available(p: Package) -> bool:
    """
    ตรวจสอบว่า package พร้อมใช้งานใน order form:
    - is_active ต้อง True
    - sale_type ต้องไม่ใช่ PRE_SALE
    - active_from/until ต้องอยู่ในช่วงเวลา (ถ้ากำหนด)
    """
    if not p.is_active:
        return False
    if p.sale_type == "PRE_SALE":
        return False
    today = date.today()
    if p.active_from and today < p.active_from:
        return False
    if p.active_until and today > p.active_until:
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
    for p in items:
        d = _to_dict(p, db)
        # เพิ่ม status badge: Active / Inactive / Expired / Pre-sale
        d["status"] = _get_display_status(p).lower()
        # เพิ่ม is_available สำหรับ order form
        d["is_available"] = _is_available(p)
        result.append(d)

    return {"items": result, "total": total, "page": page, "page_size": page_size}


def _get_display_status(p: Package) -> str:
    """คำนวณ status badge สำหรับแสดงใน UI"""
    if not p.is_active:
        return "INACTIVE"
    today = date.today()
    if p.active_until and today > p.active_until:
        return "EXPIRED"
    if p.sale_type == "PRE_SALE":
        return "PRE_SALE"
    return "ACTIVE"


def get_package(package_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    p = db.query(Package).filter_by(id=package_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Package not found")
    d = _to_dict(p, db)
    d["status"] = _get_display_status(p).lower()
    d["is_available"] = _is_available(p)
    return d


def create_package(payload: dict, current_user: dict, db: Session) -> dict:
    partner_id = _to_uuid(current_user.get("partner_id"))
    p = Package(
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
    db.add(p)
    db.flush()

    # ถ้า branch_scope = SELECTED ให้บันทึก branch_ids ลง package_branch_scopes
    if p.branch_scope == "SELECTED" and payload.get("branch_ids"):
        for bid in payload["branch_ids"]:
            db.add(PackageBranchScope(package_id=p.id, branch_id=_to_uuid(bid)))
        db.flush()

    activity_log(db, current_user, "package.create", "package", str(p.id),
                 detail=f"Created package: {payload['name']}")
    return _to_dict(p, db)


def update_package(package_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    p = db.query(Package).filter_by(id=package_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Package not found")

    before = _to_dict(p)
    for field in ["name", "price", "is_active", "sale_type", "branch_scope"]:
        if field in payload and payload[field] is not None:
            setattr(p, field, payload[field])
    if "active_from" in payload:
        p.active_from = date.fromisoformat(payload["active_from"]) if payload["active_from"] else None
    if "active_until" in payload:
        p.active_until = date.fromisoformat(payload["active_until"]) if payload["active_until"] else None

    # อัปเดต branch scopes ถ้ามี
    if "branch_ids" in payload:
        db.query(PackageBranchScope).filter_by(package_id=package_id).delete()
        if p.branch_scope == "SELECTED" and payload["branch_ids"]:
            for bid in payload["branch_ids"]:
                db.add(PackageBranchScope(package_id=p.id, branch_id=_to_uuid(bid)))
    db.flush()

    activity_log(db, current_user, "package.edit", "package", str(package_id),
                 changes={"before": before, "after": _to_dict(p)})
    return _to_dict(p, db)


def delete_package(package_id: uuid.UUID, current_user: dict, db: Session) -> None:
    p = db.query(Package).filter_by(id=package_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Package not found")

    # INT-05: ไม่ลบ package ที่อยู่ใน order อยู่แล้ว
    in_orders = db.query(Order).filter_by(package_id=package_id).count()
    if in_orders > 0:
        raise HTTPException(
            status_code=409,
            detail="Package referenced by existing orders",
        )

    db.delete(p)
    db.flush()
    activity_log(db, current_user, "package.delete", "package", str(package_id))
