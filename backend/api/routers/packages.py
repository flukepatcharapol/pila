"""
api/routers/packages.py

Package endpoints:
  GET    /packages
  POST   /packages
  GET    /packages/:id
  PUT    /packages/:id
  DELETE /packages/:id  (409 ถ้า referenced in orders)
"""
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import packages as package_service

router = APIRouter()


class CreatePackageRequest(BaseModel):
    name: str
    hours: float
    sale_type: str = "SALE"
    price: float
    branch_scope: str = "ALL"
    branch_ids: Optional[List[str]] = None   # ใช้เมื่อ branch_scope = SELECTED
    is_active: bool = True
    active_from: Optional[str] = None
    active_until: Optional[str] = None


class UpdatePackageRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    sale_type: Optional[str] = None
    is_active: Optional[bool] = None
    branch_scope: Optional[str] = None
    branch_ids: Optional[List[str]] = None
    active_from: Optional[str] = None
    active_until: Optional[str] = None


@router.get("/packages")
def list_packages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    active_only: bool = Query(False),
    branch_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return package_service.list_packages(current_user, db, page, page_size, active_only, branch_id)


@router.post("/packages", status_code=201)
def create_package(
    body: CreatePackageRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return package_service.create_package(body.model_dump(), current_user, db)


@router.get("/packages/{package_id}")
def get_package(
    package_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return package_service.get_package(package_id, current_user, db)


@router.put("/packages/{package_id}")
def update_package(
    package_id: UUID,
    body: UpdatePackageRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return package_service.update_package(package_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/packages/{package_id}", status_code=204)
def delete_package(
    package_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    package_service.delete_package(package_id, current_user, db)
