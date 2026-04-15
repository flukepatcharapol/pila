"""
api/routers/cancel_policy.py

Cancel Policy endpoints (DB-backed):
  GET  /settings/cancel-policy           — ดู policy ของ branch ปัจจุบัน
  PUT  /settings/cancel-policy           — อัปเดต policy (owner+)
  GET  /settings/cancel-policy/:branch_id — ดู policy ของ branch ที่ระบุ
"""
import uuid
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.models.booking import CancelPolicy

router = APIRouter()


class CancelPolicyRequest(BaseModel):
    hours_before: int = 24
    return_hour: bool = True    # คืนชั่วโมงเมื่อยกเลิก
    branch_id: Optional[str] = None   # ถ้าไม่ระบุ ใช้ branch ของ current user


def _to_dict(policy: CancelPolicy) -> dict:
    return {
        "id": str(policy.id),
        "branch_id": str(policy.branch_id),
        "hours_before": policy.hours_before,
        "return_hour": policy.return_hour,
        "updated_at": str(policy.updated_at),
    }


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


@router.get("/settings/cancel-policy")
def get_cancel_policy(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดู cancel policy ของ branch ปัจจุบัน"""
    branch_id = current_user.get("branch_id")
    if not branch_id:
        return {"hours_before": 24, "return_hour": True, "branch_id": None}

    policy = db.query(CancelPolicy).filter_by(branch_id=_to_uuid(branch_id)).first()
    if not policy:
        return {"hours_before": 24, "return_hour": True, "branch_id": str(branch_id)}

    return _to_dict(policy)


@router.put("/settings/cancel-policy")
def update_cancel_policy(
    body: CancelPolicyRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """อัปเดต cancel policy — upsert ต่อ branch (OWNER+ เท่านั้น)"""
    role = current_user.get("role", "").upper()
    if role not in ("DEVELOPER", "OWNER", "BRANCH_MASTER"):
        raise HTTPException(status_code=403, detail="Forbidden")

    branch_id_str = body.branch_id or current_user.get("branch_id")

    # Owner without branch_id: find first branch of partner
    if not branch_id_str and role in ("OWNER", "DEVELOPER"):
        partner_id = _to_uuid(current_user.get("partner_id"))
        if partner_id:
            from api.models.branch import Branch
            first_branch = db.query(Branch).filter_by(partner_id=partner_id).first()
            if first_branch:
                branch_id_str = str(first_branch.id)

    if not branch_id_str:
        raise HTTPException(status_code=400, detail="branch_id is required")

    branch_id = _to_uuid(branch_id_str)
    user_id = _to_uuid(current_user.get("sub"))

    policy = db.query(CancelPolicy).filter_by(branch_id=branch_id).first()
    if policy:
        policy.hours_before = body.hours_before
        policy.return_hour = body.return_hour
        policy.updated_by = user_id
        policy.updated_at = datetime.utcnow()
    else:
        policy = CancelPolicy(
            branch_id=branch_id,
            hours_before=body.hours_before,
            return_hour=body.return_hour,
            updated_by=user_id,
        )
        db.add(policy)

    db.flush()
    return _to_dict(policy)


@router.get("/settings/cancel-policy/{branch_id}")
def get_cancel_policy_by_branch(
    branch_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดู cancel policy ของ branch ที่ระบุ"""
    policy = db.query(CancelPolicy).filter_by(branch_id=branch_id).first()
    if not policy:
        return {"hours_before": 24, "return_hour": True, "branch_id": str(branch_id)}
    return _to_dict(policy)
