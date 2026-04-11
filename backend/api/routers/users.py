"""api/routers/users.py"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import users as user_service

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: Optional[str] = None
    pin: Optional[str] = None
    role: str = "ADMIN"
    branch_id: Optional[str] = None
    is_active: bool = True


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[str] = None
    is_active: Optional[bool] = None


class ChangeRoleRequest(BaseModel):
    role: str


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return user_service.list_users(current_user, db, page, page_size)


@router.post("/users", status_code=201)
def create_user(
    body: CreateUserRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return user_service.create_user(body.model_dump(), current_user, db)


@router.get("/users/{user_id}")
def get_user(
    user_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return user_service.get_user(user_id, current_user, db)


@router.put("/users/{user_id}")
def update_user(
    user_id: UUID,
    body: UpdateUserRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return user_service.update_user(user_id, body.model_dump(exclude_none=True), current_user, db)


@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: UUID,
    body: ChangeRoleRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return user_service.change_user_role(user_id, body.role, current_user, db)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return user_service.delete_user(user_id, current_user, db)
