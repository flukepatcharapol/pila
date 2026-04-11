"""
api/models/google_integration.py

Models สำหรับ Google OAuth + Drive integration:
  GoogleToken         — เก็บ access/refresh token ต่อ user
  SignaturePrintFile  — บันทึกไฟล์ที่ generate ขึ้น Google Sheets
  UserPreference      — settings ของ user (language, dark mode)
"""
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, Boolean, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class GoogleToken(Base):
    """
    เก็บ Google OAuth token ต่อ user
    access_token + refresh_token ควร encrypt at rest ใน production
    """
    __tablename__ = "google_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id: unique — แต่ละ user มี Google token ได้แค่ 1 ชุด
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    connected_email: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SignaturePrintFile(Base):
    """
    บันทึกไฟล์ Google Sheet ที่ generate สำหรับ signature print
    file_url: shareable link, file_id: Google Drive file ID
    """
    __tablename__ = "signature_print_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    # generated_by: user ที่กด generate
    generated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class UserPreference(Base):
    """
    Settings ของแต่ละ user — persist ข้าม session
    language: TH|EN, dark_mode: True|False
    """
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id: unique — 1 user มี preference ได้แค่ 1 แถว
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    # language: TH|EN (เดิม VARCHAR — เปลี่ยนเป็น enum-like string)
    language: Mapped[str] = mapped_column(String(5), default="TH", nullable=False)
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
