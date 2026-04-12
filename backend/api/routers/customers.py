"""
api/routers/customers.py

Customer endpoints:
  GET    /customers
  POST   /customers
  GET    /customers/:id
  PUT    /customers/:id
  DELETE /customers/:id
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import customers as customer_service

router = APIRouter()


# ─── Schemas ───────────────────────────────────────────────────────────────────

class CreateCustomerRequest(BaseModel):
    branch_id: str
    source_type_id: str
    first_name: str
    last_name: str
    nickname: Optional[str] = None
    contact_channel: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    line_id: Optional[str] = None
    birthday: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    trainer_id: Optional[str] = None
    caretaker_id: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_length(cls, v):
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and v != "":
            import re
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError("Invalid email format")
        return v

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v):
        if v is not None and v != "":
            from datetime import date
            try:
                bday = date.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid date format for birthday")
            if bday > date.today():
                raise ValueError("Birthday cannot be in the future")
        return v


class UpdateCustomerRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    contact_channel: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    line_id: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    trainer_id: Optional[str] = None
    caretaker_id: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and v != "":
            import re
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError("Invalid email format")
        return v


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/customers")
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return customer_service.list_customers(
        current_user=current_user,
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        branch=branch,
    )


@router.post("/customers", status_code=201)
def create_customer(
    body: CreateCustomerRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return customer_service.create_customer(body.model_dump(), current_user, db)


@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return customer_service.get_customer(customer_id, current_user, db)


@router.put("/customers/{customer_id}")
def update_customer(
    customer_id: UUID,
    body: UpdateCustomerRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return customer_service.update_customer(customer_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(
    customer_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    customer_service.delete_customer(customer_id, current_user, db)
