"""
api/routers/branches.py

Branch endpoints:
  GET    /branches
  POST   /branches
  GET    /branches/:id
  PUT    /branches/:id
  DELETE /branches/:id                    (409 ถ้ามี customers)
  GET    /branches/:id/source-types
  POST   /branches/:id/source-types
  PUT    /branches/:id/source-types/:stid
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import branches as branch_service

router = APIRouter()


class CreateBranchRequest(BaseModel):
    name: str
    prefix: str
    opening_time: Optional[str] = "09:00"
    closing_time: Optional[str] = "21:00"
    is_active: bool = True


class UpdateBranchRequest(BaseModel):
    name: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    is_active: Optional[bool] = None


class CreateSourceTypeRequest(BaseModel):
    label: str
    code: str


class UpdateSourceTypeRequest(BaseModel):
    label: Optional[str] = None


@router.get("/branches")
def list_branches(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return branch_service.list_branches(current_user, db)


@router.post("/branches", status_code=201)
def create_branch(
    body: CreateBranchRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return branch_service.create_branch(body.model_dump(), current_user, db)


@router.get("/branches/{branch_id}")
def get_branch(
    branch_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return branch_service.get_branch(branch_id, current_user, db)


@router.put("/branches/{branch_id}")
def update_branch(
    branch_id: UUID,
    body: UpdateBranchRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return branch_service.update_branch(branch_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/branches/{branch_id}", status_code=204)
def delete_branch(
    branch_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ลบ branch — คืน 409 ถ้ายังมี customers (INT-03)"""
    branch_service.delete_branch(branch_id, current_user, db)


@router.get("/branches/{branch_id}/source-types")
def list_source_types(
    branch_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return branch_service.list_source_types(branch_id, db)


@router.post("/branches/{branch_id}/source-types", status_code=201)
def create_source_type(
    branch_id: UUID,
    body: CreateSourceTypeRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return branch_service.create_source_type(branch_id, body.model_dump(), current_user, db)


@router.put("/branches/{branch_id}/source-types/{source_type_id}")
def update_source_type(
    branch_id: UUID,
    source_type_id: UUID,
    body: UpdateSourceTypeRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return branch_service.update_source_type(branch_id, source_type_id, body.model_dump(exclude_none=True), current_user, db)
