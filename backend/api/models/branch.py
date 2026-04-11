import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Boolean, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # prefix: รหัสสาขา เช่น BPY, BCC — ใช้ใน customer_code
    prefix: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    opening_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    closing_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
