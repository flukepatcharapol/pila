"""
api/services/branches.py

Business logic สำหรับ Branch CRUD + Source Types
"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.branch import Branch
from api.models.user import SourceType
from api.models.customer import Customer
from api.services.activity_log import log as activity_log

MAX_PAGE_SIZE = 100


def _to_uuid(val) -> uuid.UUID | None:
    if not val:
        return None
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


def _to_dict(b: Branch) -> dict:
    return {
        "id": str(b.id),
        "partner_id": str(b.partner_id),
        "name": b.name,
        "prefix": b.prefix,
        "opening_time": b.opening_time,
        "closing_time": b.closing_time,
        "is_active": b.is_active,
    }


def list_branches(current_user: dict, db: Session) -> dict:
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    query = db.query(Branch)
    if role != "DEVELOPER" and partner_id:
        query = query.filter(Branch.partner_id == _to_uuid(partner_id))
    items = query.all()
    return {"items": [_to_dict(b) for b in items], "total": len(items)}


def get_branch(branch_id: uuid.UUID, current_user: dict, db: Session) -> dict:
    b = db.query(Branch).filter_by(id=branch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Branch not found")
    return _to_dict(b)


def create_branch(payload: dict, current_user: dict, db: Session) -> dict:
    role = current_user.get("role", "").upper()
    if role not in ("OWNER", "DEVELOPER"):
        raise HTTPException(status_code=403, detail="Forbidden")

    partner_id = _to_uuid(current_user.get("partner_id"))
    b = Branch(
        partner_id=partner_id,
        name=payload["name"],
        prefix=payload["prefix"].upper(),
        opening_time=payload.get("opening_time", "09:00"),
        closing_time=payload.get("closing_time", "21:00"),
        is_active=payload.get("is_active", True),
    )
    db.add(b)
    db.flush()
    activity_log(db, current_user, "branch.create", "branch", str(b.id),
                 detail=f"Created branch: {payload['name']}")
    return _to_dict(b)


def update_branch(branch_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    role = current_user.get("role", "").upper()
    if role not in ("OWNER", "DEVELOPER", "BRANCH_MASTER"):
        raise HTTPException(status_code=403, detail="Forbidden")

    b = db.query(Branch).filter_by(id=branch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Branch not found")

    before = _to_dict(b)
    for field in ["name", "opening_time", "closing_time", "is_active"]:
        if field in payload and payload[field] is not None:
            setattr(b, field, payload[field])

    # Handle source_types updates (e.g. change code/label)
    source_types_list = payload.get("source_types")
    if source_types_list:
        for st_data in source_types_list:
            st_id = _to_uuid(st_data.get("id"))
            if st_id:
                st = db.query(SourceType).filter_by(id=st_id, branch_id=branch_id).first()
                if st:
                    if "code" in st_data and st_data["code"]:
                        st.code = st_data["code"].upper()
                    if "label" in st_data and st_data["label"]:
                        st.label = st_data["label"]

    db.flush()

    activity_log(db, current_user, "branch.edit", "branch", str(branch_id),
                 changes={"before": before, "after": _to_dict(b)})
    return _to_dict(b)


def delete_branch(branch_id: uuid.UUID, current_user: dict, db: Session) -> None:
    b = db.query(Branch).filter_by(id=branch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Branch not found")

    # INT-03: ไม่ลบ branch ที่ยังมี customer อยู่
    customer_count = db.query(Customer).filter_by(branch_id=branch_id).count()
    if customer_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete branch with existing customers",
        )

    db.delete(b)
    db.flush()
    activity_log(db, current_user, "branch.delete", "branch", str(branch_id))


# ─── Source Types ─────────────────────────────────────────────────────────────


def list_source_types(branch_id: uuid.UUID, db: Session) -> dict:
    items = db.query(SourceType).filter_by(branch_id=branch_id).all()
    return {
        "items": [
            {"id": str(s.id), "branch_id": str(s.branch_id), "label": s.label, "code": s.code}
            for s in items
        ]
    }


def create_source_type(branch_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    # ตรวจสอบว่า code ไม่ซ้ำใน branch เดียวกัน
    existing = db.query(SourceType).filter_by(branch_id=branch_id, code=payload["code"]).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Source code '{payload['code']}' already exists in this branch")

    s = SourceType(
        branch_id=branch_id,
        label=payload["label"],
        code=payload["code"].upper(),
    )
    db.add(s)
    db.flush()
    return {"id": str(s.id), "branch_id": str(s.branch_id), "label": s.label, "code": s.code}


def update_source_type(branch_id: uuid.UUID, source_type_id: uuid.UUID, payload: dict, current_user: dict, db: Session) -> dict:
    s = db.query(SourceType).filter_by(id=source_type_id, branch_id=branch_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Source type not found")

    for field in ["label"]:
        if field in payload and payload[field] is not None:
            setattr(s, field, payload[field])

    # หมายเหตุ: เปลี่ยน code ไม่ได้ หลัง create แล้ว (customer_code เดิมอิงจาก code)
    db.flush()
    return {"id": str(s.id), "branch_id": str(s.branch_id), "label": s.label, "code": s.code}
