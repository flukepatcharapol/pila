import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class ActivityLog(Base):
    """Audit log สำหรับทุก write operation — บันทึก before/after snapshot"""
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id: user ที่ทำ action (เดิมชื่อ actor_id — เปลี่ยนให้ consistent)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    # action: เช่น 'customer.create', 'order.edit', 'session.deduct'
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    # changes: JSON snapshot ของ before/after เช่น {"before": {...}, "after": {...}}
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # detail: human-readable description (fallback เมื่อ changes ไม่ครบ)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
