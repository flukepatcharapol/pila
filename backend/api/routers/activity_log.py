"""api/routers/activity_log.py"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.models.activity_log import ActivityLog

router = APIRouter()


@router.get("/activity-log")
def list_activity_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    action: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    from api.dependencies.branch_scope import get_user_branch_ids
    import uuid as _uuid
    query = db.query(ActivityLog)
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")

    if role == "OWNER":
        pid = None
        if partner_id:
            try:
                pid = _uuid.UUID(str(partner_id))
            except (ValueError, AttributeError, TypeError):
                pid = None
        if pid:
            query = query.filter(ActivityLog.partner_id == pid)
    elif role != "DEVELOPER":
        allowed = get_user_branch_ids(current_user)
        if allowed:
            query = query.filter(ActivityLog.branch_id.in_(allowed))
        else:
            query = query.filter(ActivityLog.id == _uuid.UUID(int=0))

    if action:
        query = query.filter(ActivityLog.action.ilike(f"%{action}%"))
    if target_id:
        query = query.filter(ActivityLog.target_id == target_id)

    total = query.count()
    items = query.order_by(ActivityLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": str(log_entry.id),
                "user_id": str(log_entry.user_id) if log_entry.user_id else None,
                "action": log_entry.action,
                "target_id": log_entry.target_id,
                "target_type": log_entry.target_type,
                "detail": log_entry.detail,
                "created_at": str(log_entry.created_at),
                "timestamp": str(log_entry.created_at),  # alias สำหรับ created_at
            }
            for log_entry in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
