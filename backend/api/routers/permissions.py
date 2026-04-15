"""
api/routers/permissions.py

Permission endpoints:
  GET  /permissions                       — ดู permission matrix (roles ที่ต่ำกว่า current user)
  PUT  /permissions                       — อัปเดต permission (branch_master+)
  GET  /permissions/feature-toggles      — ดู feature toggles
  PUT  /permissions/feature-toggles      — อัปเดต feature toggle (owner+)
  GET  /permissions/:role                — ดู permissions ของ role เดียว
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import permissions as permission_service

router = APIRouter()


class UpdatePermissionRequest(BaseModel):
    role: str
    action: str
    branch_id: Optional[str] = None
    # Accept both "feature_name"/"is_allowed" and "resource"/"allowed" (legacy)
    feature_name: Optional[str] = None
    resource: Optional[str] = None
    is_allowed: Optional[bool] = None
    allowed: Optional[bool] = None


class UpdateFeatureToggleRequest(BaseModel):
    feature_name: str
    is_enabled: bool


@router.get("/permissions")
def list_permissions(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return permission_service.get_permission_matrix(current_user, db)


@router.put("/permissions")
def update_permission(
    body: UpdatePermissionRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return permission_service.update_permission(body.model_dump(), current_user, db)


@router.get("/permissions/feature-toggles")
def list_feature_toggles(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return permission_service.get_feature_toggles(current_user, db)


@router.put("/permissions/feature-toggles")
def update_feature_toggle(
    body: UpdateFeatureToggleRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return permission_service.update_feature_toggle(body.model_dump(), current_user, db)


@router.get("/permissions/{role}")
def get_permissions_by_role(
    role: str,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดู permissions ของ role เดียว"""
    from api.models.permission import PermissionMatrix
    items = db.query(PermissionMatrix).filter_by(role=role.upper()).all()
    return {
        "role": role.upper(),
        "permissions": [
            {
                "feature_name": matrix_row.feature_name,
                "action": matrix_row.action,
                "is_allowed": matrix_row.is_allowed,
            }
            for matrix_row in items
        ],
    }
