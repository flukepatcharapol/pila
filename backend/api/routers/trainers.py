"""
api/routers/trainers.py

Trainer endpoints:
  GET    /trainers
  POST   /trainers
  GET    /trainers/:id
  PUT    /trainers/:id
  DELETE /trainers/:id  (409 ถ้ามี active customer/booking)
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import trainers as trainer_service

router = APIRouter()


class CreateTrainerRequest(BaseModel):
    branch_id: str
    name: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    profile_photo_url: Optional[str] = None
    status: str = "ACTIVE"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and v != "":
            import re
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError("Invalid email format")
        return v


class UpdateTrainerRequest(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    profile_photo_url: Optional[str] = None
    status: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and v != "":
            import re
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError("Invalid email format")
        return v


@router.get("/trainers")
def list_trainers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return trainer_service.list_trainers(current_user, db, page, page_size, status)


@router.post("/trainers", status_code=201)
def create_trainer(
    body: CreateTrainerRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return trainer_service.create_trainer(body.model_dump(), current_user, db)


@router.get("/trainers/{trainer_id}")
def get_trainer(
    trainer_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return trainer_service.get_trainer(trainer_id, current_user, db)


@router.put("/trainers/{trainer_id}")
def update_trainer(
    trainer_id: UUID,
    body: UpdateTrainerRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return trainer_service.update_trainer(trainer_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/trainers/{trainer_id}", status_code=204)
def delete_trainer(
    trainer_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    trainer_service.delete_trainer(trainer_id, current_user, db)
