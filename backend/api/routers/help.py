"""
api/routers/help.py

Help endpoints:
  GET /help/manual    — user manual (role-specific sections)
  GET /help/line-qr   — LINE QR codes
  GET /help/faq       — FAQ sections
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified

router = APIRouter()

# Static help content — ในระบบจริงดึงจาก DB (help_content table)
# แต่ละ section ระบุ visible_to เพื่อกรองตาม role
_MANUAL_SECTIONS = [
    {
        "id": "customers",
        "title_th": "การจัดการลูกค้า",
        "title_en": "Customer Management",
        "visible_to": ["DEVELOPER", "OWNER", "BRANCH_MASTER", "ADMIN"],
        "content_th": "การเพิ่ม แก้ไข และจัดการข้อมูลลูกค้า รหัสลูกค้าสร้างอัตโนมัติจาก branch + source type",
    },
    {
        "id": "bookings",
        "title_th": "การจองและตารางงาน",
        "title_en": "Booking & Schedule",
        "visible_to": ["DEVELOPER", "OWNER", "BRANCH_MASTER", "ADMIN", "TRAINER"],
        "content_th": "การสร้างและยืนยันการนัดหมาย ตารางงาน trainer",
    },
    {
        "id": "orders",
        "title_th": "การจัดการ Order",
        "title_en": "Order Management",
        "visible_to": ["DEVELOPER", "OWNER", "BRANCH_MASTER", "ADMIN"],
        "content_th": "การสร้าง order และบันทึกการชำระเงิน",
    },
    {
        "id": "customer_hours",
        "title_th": "ชั่วโมงลูกค้า",
        "title_en": "Customer Hours",
        "visible_to": ["DEVELOPER", "OWNER", "BRANCH_MASTER", "ADMIN", "TRAINER"],
        "content_th": "การหักชั่วโมงและดูประวัติธุรกรรม",
    },
    {
        "id": "users",
        "title_th": "จัดการ User",
        "title_en": "User Management",
        "visible_to": ["DEVELOPER", "OWNER", "BRANCH_MASTER"],
        "content_th": "การสร้างและจัดการ user ในระบบ",
    },
    {
        "id": "permissions",
        "title_th": "จัดการสิทธิ์",
        "title_en": "Permission Management",
        "visible_to": ["DEVELOPER", "OWNER"],
        "content_th": "การกำหนดสิทธิ์การเข้าถึงของแต่ละ role",
    },
    {
        "id": "reports",
        "title_th": "รายงานและ Dashboard",
        "title_en": "Reports & Dashboard",
        "visible_to": ["DEVELOPER", "OWNER", "BRANCH_MASTER", "ADMIN", "TRAINER"],
        "content_th": "ดูสถิติและรายงานต่างๆ",
    },
]

_FAQ = [
    {"question": "วิธี reset PIN คืออะไร?", "answer": "ไปที่หน้า login แล้วกด 'ลืม PIN' → รับ OTP ทาง email"},
    {"question": "รหัสลูกค้าสร้างอย่างไร?", "answer": "สร้างอัตโนมัติจาก branch prefix + source code + running number เช่น BPY-MKT001"},
    {"question": "จะ export รายงานได้อย่างไร?", "answer": "ใช้ Signature Print เชื่อม Google Drive แล้ว generate Google Sheet"},
    {"question": "หากชั่วโมงติดลบจะเกิดอะไรขึ้น?", "answer": "ระบบจะบล็อกการหักชั่วโมงทันที ต้องเติม order ก่อน"},
]


@router.get("/help/manual")
def get_manual(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    ดู user manual — กรองเฉพาะ section ที่ role นี้เข้าถึงได้
    เหตุผล: ไม่แสดง section ที่ user ไม่มีสิทธิ์ เพื่อไม่ให้งง
    """
    role = current_user.get("role", "")
    visible_sections = [
        section for section in _MANUAL_SECTIONS
        if role in section["visible_to"]
    ]
    return {
        "title": "Pila Studio — คู่มือการใช้งาน",
        "version": "1.0",
        "role": role,
        "sections": visible_sections,
    }


@router.get("/help/line-qr")
def get_line_qr(
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    ดู LINE QR codes — developer QR + branch QR ตาม branch ของ user
    ในระบบจริงดึงจาก line_qr_codes table
    """
    branch_id = current_user.get("branch_id")

    developer_qr_url = "/static/qr/developer.png"
    branch_qr_url = f"/static/qr/branch_{branch_id}.png" if branch_id else None

    return {
        "developer_qr_url": developer_qr_url,
        "branch_qr_url": branch_qr_url,
    }


@router.get("/help/faq")
def get_faq(
    current_user: dict = Depends(require_pin_verified),
):
    """FAQ sections — expandable"""
    return {"items": _FAQ}
