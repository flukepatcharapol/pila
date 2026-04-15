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
    query = db.query(ActivityLog)
    role = current_user.get("role", "")
    partner_id = current_user.get("partner_id")
    branch_id = current_user.get("branch_id")

    if role not in ("DEVELOPER", "OWNER"):
        if branch_id:
            import uuid as _uuid
            try:
                query = query.filter(ActivityLog.branch_id == _uuid.UUID(str(branch_id)))
            except (ValueError, AttributeError):
                pass

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
