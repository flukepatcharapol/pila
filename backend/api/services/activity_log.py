"""
api/services/activity_log.py

Helper สำหรับสร้าง ActivityLog entry — ใช้ในทุก service ที่มี write operation
เหตุผลที่แยกออกมา: ทุก service import ที่เดียว ไม่ต้องเขียน ActivityLog(...) ซ้ำๆ
"""
import uuid
from sqlalchemy.orm import Session
from api.models.activity_log import ActivityLog


def _to_uuid(raw_value) -> uuid.UUID | None:
    """แปลง string/UUID → uuid.UUID, คืน None ถ้าค่าเป็น None หรือ empty"""
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def log(
    db: Session,
    current_user: dict,
    action: str,
    target_type: str,
    target_id: str,
    changes: dict | None = None,
    detail: str | None = None,
) -> None:
    """
    สร้าง ActivityLog 1 แถว

    Parameters:
      action      — 'customer.create', 'order.edit', 'session.deduct' ฯลฯ
      target_type — 'customer', 'order', 'booking' ฯลฯ
      target_id   — ID ของ record ที่ถูก affect (เป็น str เสมอ)
      changes     — {"before": {...}, "after": {...}} snapshot (optional)
      detail      — human-readable fallback เมื่อ changes ไม่ครบ
    """
    sub = current_user.get("sub")
    partner_id = current_user.get("partner_id")

    # Pick a representative branch for the log entry:
    #   - unrestricted (OWNER/DEVELOPER) → None
    #   - scoped role → first branch in the user's list (None if no branches)
    from api.dependencies.branch_scope import get_user_branch_ids
    allowed = get_user_branch_ids(current_user)
    branch_id = None if not allowed else allowed[0]

    entry = ActivityLog(
        user_id=_to_uuid(sub),
        partner_id=_to_uuid(partner_id),
        branch_id=branch_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        changes=changes,
        detail=detail,
    )
    db.add(entry)
    db.flush()
