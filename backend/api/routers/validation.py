"""api/routers/validation.py — Input validation endpoints"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from typing import Optional
import re

from api.dependencies.auth import require_pin_verified

router = APIRouter()


class ValidateCustomerRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def check_name_length(cls, v):
        if v and len(v) > 100:
            raise ValueError("Name exceeds maximum length of 100 characters")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if v and not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Invalid email format")
        return v


@router.post("/validate/customer")
def validate_customer_payload(body: ValidateCustomerRequest, current_user: dict = Depends(require_pin_verified)):
    return {"valid": True, "message": "Payload is valid"}


@router.post("/validate/email")
def validate_email(body: dict, current_user: dict = Depends(require_pin_verified)):
    email = body.get("email", "")
    valid = bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email))
    return {"email": email, "valid": valid}


@router.post("/validate/phone")
def validate_phone(body: dict, current_user: dict = Depends(require_pin_verified)):
    phone = body.get("phone", "")
    valid = bool(re.match(r"^[0-9+\-\s]{7,15}$", phone))
    return {"phone": phone, "valid": valid}
