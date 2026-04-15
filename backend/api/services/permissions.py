"""
api/services/permissions.py

Business logic สำหรับ PermissionMatrix + FeatureToggle
"""
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.models.permission import PermissionMatrix, FeatureToggle
from api.services.activity_log import log as activity_log


# Role hierarchy: higher index = higher rank
ROLE_HIERARCHY = ["TRAINER", "ADMIN", "BRANCH_MASTER", "OWNER", "DEVELOPER"]
ROLE_RANK = {role: rank_index for rank_index, role in enumerate(ROLE_HIERARCHY)}


def _to_uuid(raw_value) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (ValueError, AttributeError):
        return None


def _get_visible_roles(role: str) -> list[str]:
    """คืน list ของ roles ที่ current role สามารถดู/จัดการได้ (เฉพาะ roles ที่ต่ำกว่า)"""
    rank = ROLE_RANK.get(role.upper(), -1)
    return [hierarchy_role.lower() for hierarchy_role in ROLE_HIERARCHY if ROLE_RANK[hierarchy_role] < rank]


def _check_permission_access(current_role: str, target_role: str = None):
    """ตรวจสอบว่า current_role สามารถจัดการ permissions ได้หรือไม่"""
    role = current_role.upper()
    if role not in ("DEVELOPER", "OWNER", "BRANCH_MASTER"):
        raise HTTPException(status_code=403, detail="Forbidden")

    if target_role:
        current_rank = ROLE_RANK.get(role, -1)
        target_rank = ROLE_RANK.get(target_role.upper(), -1)
        if target_rank >= current_rank:
            raise HTTPException(
                status_code=403,
                detail="Cannot manage permissions for equal or higher role",
            )


def get_permission_matrix(current_user: dict, db: Session) -> dict:
    """
    ดึง permission matrix — คืนเฉพาะ roles ที่ต่ำกว่า current user
    Format: {role_name: {feature_name: {action: bool}}}
    """
    role = current_user.get("role", "").upper()
    _check_permission_access(role)

    visible_roles = _get_visible_roles(role)

    items = db.query(PermissionMatrix).filter(
        PermissionMatrix.role.in_([vr.upper() for vr in visible_roles])
    ).all()

    # Build hierarchical response
    result = {rn: {} for rn in visible_roles}
    for matrix_row in items:
        rn = matrix_row.role.lower()
        if rn not in result:
            continue
        if matrix_row.feature_name not in result[rn]:
            result[rn][matrix_row.feature_name] = {}
        result[rn][matrix_row.feature_name][matrix_row.action.lower()] = matrix_row.is_allowed

    return result


def update_permission(payload: dict, current_user: dict, db: Session) -> dict:
    """อัปเดต permission — upsert ตาม branch_id + role + feature_name + action"""
    role = current_user.get("role", "").upper()

    target_role = payload["role"].upper()
    _check_permission_access(role, target_role)

    # Accept "resource"/"allowed" as aliases for "feature_name"/"is_allowed"
    feature_name = payload.get("feature_name") or payload.get("resource")
    if feature_name is None:
        raise HTTPException(status_code=422, detail="feature_name or resource is required")

    if "is_allowed" in payload:
        is_allowed = payload["is_allowed"]
    elif "allowed" in payload:
        is_allowed = payload["allowed"]
    else:
        raise HTTPException(status_code=422, detail="is_allowed or allowed is required")

    action = payload["action"].upper()
    branch_id = _to_uuid(payload.get("branch_id"))
    user_id = _to_uuid(current_user.get("sub"))

    existing = db.query(PermissionMatrix).filter_by(
        branch_id=branch_id, role=target_role, feature_name=feature_name, action=action
    ).first()

    if existing:
        existing.is_allowed = is_allowed
        existing.updated_by = user_id
        db.flush()
        permission_record = existing
    else:
        permission_record = PermissionMatrix(
            branch_id=branch_id,
            role=target_role,
            feature_name=feature_name,
            action=action,
            is_allowed=is_allowed,
            updated_by=user_id,
        )
        db.add(permission_record)
        db.flush()

    activity_log(
        db, current_user, "permission.update", "permission", str(permission_record.id),
        detail=f"{target_role}.{feature_name}.{action} = {is_allowed}",
    )

    return {
        "id": str(permission_record.id),
        "branch_id": str(permission_record.branch_id) if permission_record.branch_id else None,
        "role": permission_record.role,
        "feature_name": permission_record.feature_name,
        "action": permission_record.action,
        "is_allowed": permission_record.is_allowed,
    }


def check_permission(db: Session, role: str, feature_name: str, action: str) -> bool:
    """
    ตรวจสอบ permission จาก matrix
    Default: True (อนุญาต) ถ้าไม่มี record
    """
    perm = db.query(PermissionMatrix).filter_by(
        role=role.upper(), feature_name=feature_name, action=action.upper()
    ).first()
    if perm and not perm.is_allowed:
        return False
    return True


def get_feature_toggles(current_user: dict, db: Session) -> dict:
    """ดึง feature toggles ทั้งหมดของ partner"""
    partner_id = current_user.get("partner_id")
    role = current_user.get("role", "")

    query = db.query(FeatureToggle)
    if role != "DEVELOPER" and partner_id:
        query = query.filter(FeatureToggle.partner_id == _to_uuid(partner_id))

    items = query.all()
    return {
        "items": [
            {
                "id": str(feature_toggle.id),
                "partner_id": str(feature_toggle.partner_id),
                "feature_name": feature_toggle.feature_name,
                "is_enabled": feature_toggle.is_enabled,
            }
            for feature_toggle in items
        ]
    }


def update_feature_toggle(payload: dict, current_user: dict, db: Session) -> dict:
    """เปิด/ปิด feature toggle — upsert ตาม partner_id + feature_name"""
    partner_id = _to_uuid(current_user.get("partner_id"))
    feature_name = payload["feature_name"]
    is_enabled = payload["is_enabled"]

    user_id = _to_uuid(current_user.get("sub"))

    existing = db.query(FeatureToggle).filter_by(
        partner_id=partner_id, feature_name=feature_name
    ).first()

    if existing:
        existing.is_enabled = is_enabled
        existing.updated_by = user_id
        db.flush()
        feature_toggle = existing
    else:
        feature_toggle = FeatureToggle(
            partner_id=partner_id,
            feature_name=feature_name,
            is_enabled=is_enabled,
            updated_by=user_id,
        )
        db.add(feature_toggle)
        db.flush()

    activity_log(
        db, current_user, "feature_toggle.update", "feature_toggle", str(feature_toggle.id),
        detail=f"{feature_name} = {is_enabled}",
    )

    return {
        "id": str(feature_toggle.id),
        "partner_id": str(feature_toggle.partner_id),
        "feature_name": feature_toggle.feature_name,
        "is_enabled": feature_toggle.is_enabled,
    }


def check_feature_enabled(feature_name: str, partner_id, db: Session) -> bool:
    """
    ตรวจสอบว่า feature เปิดอยู่หรือไม่
    Default True ถ้าไม่มีใน DB (เพื่อ backward compatibility)
    """
    pid = _to_uuid(partner_id)
    toggle = db.query(FeatureToggle).filter_by(
        partner_id=pid, feature_name=feature_name
    ).first()
    return toggle.is_enabled if toggle else True
