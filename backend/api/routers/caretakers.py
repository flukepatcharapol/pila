"""
api/routers/caretakers.py

Caretaker endpoints:
  GET    /caretakers
  POST   /caretakers
  GET    /caretakers/:id
  PUT    /caretakers/:id
  DELETE /caretakers/:id
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import caretakers as caretaker_service

router = APIRouter()


class CreateCaretakerRequest(BaseModel):
    branch_id: str
    name: str
    email: Optional[str] = None
    status: str = "ACTIVE"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and v != "":
            import re
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError("Invalid email format")
        return v


class UpdateCaretakerRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and v != "":
            import re
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError("Invalid email format")
        return v


@router.get("/caretakers")
def list_caretakers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return caretaker_service.list_caretakers(current_user, db, page, page_size)


@router.post("/caretakers", status_code=201)
def create_caretaker(
    body: CreateCaretakerRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return caretaker_service.create_caretaker(body.model_dump(), current_user, db)


@router.get("/caretakers/{caretaker_id}")
def get_caretaker(
    caretaker_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return caretaker_service.get_caretaker(caretaker_id, current_user, db)


@router.put("/caretakers/{caretaker_id}")
def update_caretaker(
    caretaker_id: UUID,
    body: UpdateCaretakerRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return caretaker_service.update_caretaker(caretaker_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/caretakers/{caretaker_id}", status_code=204)
def delete_caretaker(
    caretaker_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    caretaker_service.delete_caretaker(caretaker_id, current_user, db)
