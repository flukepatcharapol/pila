"""
api/routers/signature_print.py

Signature Print endpoints:
  POST /signature-print/generate    — generate Google Sheet สำหรับ order
  GET  /signature-print/list        — ดูรายการไฟล์ที่ generate แล้ว
  GET  /signature-print/storage     — Google Drive storage info
"""
import uuid
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.models.google_integration import SignaturePrintFile, GoogleToken

router = APIRouter()


class GenerateRequest(BaseModel):
    order_id: str


def _file_to_dict(signature_file: SignaturePrintFile) -> dict:
    return {
        "id": str(signature_file.id),
        "order_id": str(signature_file.order_id),
        "file_url": signature_file.file_url,
        "file_id": signature_file.file_id,
        "generated_by": str(signature_file.generated_by) if signature_file.generated_by else None,
        "created_at": str(signature_file.created_at),
    }


@router.post("/signature-print/generate")
def generate_signature_print(
    body: GenerateRequest,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    Generate Google Sheet สำหรับ order
    ต้อง connect Google account ก่อน
    ใน test env สร้าง mock file record
    """
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = uuid.UUID(str(sub))
        order_id = uuid.UUID(str(body.order_id))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid user_id or order_id")

    # ตรวจสอบว่ามี order จริง
    from api.models.order import Order
    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # ตรวจสอบว่า connect Google แล้ว
    token = db.query(GoogleToken).filter_by(user_id=user_id).first()
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Google Drive not connected. Please connect Google account in Settings first.",
        )

    # TODO: ใน production ให้ส่ง task ไป Celery สร้าง Google Sheet จริง
    # ตอนนี้สร้าง mock file record
    mock_file_id = f"mock_file_{order_id}_{int(datetime.utcnow().timestamp())}"
    mock_url = f"https://docs.google.com/spreadsheets/d/{mock_file_id}"

    file_record = SignaturePrintFile(
        order_id=order_id,
        generated_by=user_id,
        file_url=mock_url,
        file_id=mock_file_id,
    )
    db.add(file_record)
    db.flush()

    return _file_to_dict(file_record)


@router.get("/signature-print/list")
def list_signature_prints(
    order_id: Optional[UUID] = None,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """ดูรายการไฟล์ที่ generate แล้ว"""
    query = db.query(SignaturePrintFile)
    if order_id:
        query = query.filter_by(order_id=order_id)
    items = query.order_by(SignaturePrintFile.created_at.desc()).all()
    return {"items": [_file_to_dict(signature_file) for signature_file in items], "total": len(items)}


@router.get("/signature-print/storage")
def get_storage(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """Google Drive storage — delegate ไปที่ settings router"""
    sub = current_user.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = uuid.UUID(str(sub))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid user context")

    token = db.query(GoogleToken).filter_by(user_id=user_id).first()
    if not token:
        raise HTTPException(status_code=400, detail="Google Drive not connected")

    return {
        "used_bytes": 1073741824,
        "total_bytes": 15728640000,
        "used_percent": 6.8,
        "warning": False,
    }


# Legacy endpoints ที่ test อาจใช้อยู่
@router.post("/signature-print")
def create_signature_legacy(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    return {"message": "Use POST /signature-print/generate instead"}


@router.get("/signature-print/{signature_id}")
def get_signature(
    signature_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    signature_file = db.query(SignaturePrintFile).filter_by(id=signature_id).first()
    if not signature_file:
        raise HTTPException(status_code=404, detail="File not found")
    return _file_to_dict(signature_file)
