import uuid
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Numeric, Boolean, Date, DateTime, Text, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    source_type_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_types.id"), nullable=True)
    trainer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trainers.id"), nullable=True)
    caretaker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("caretakers.id"), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    customer_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_channel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    line_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # is_duplicate: True เมื่อลูกค้าคนนี้อาจซ้ำกับคนอื่น (ใช้ flag แทน hard-delete)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CustomerCodeCounter(Base):
    """Counter สำหรับ generate customer_code ต่อ branch+source_type แบบ atomic"""
    __tablename__ = "customer_code_counters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    # source_type_id: FK ไปที่ source_types เพื่อให้ counter แยกต่อ branch+source combo
    source_type_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_types.id"), nullable=True)
    source_code: Mapped[str] = mapped_column(String(10), nullable=False)
    last_sequence: Mapped[int] = mapped_column(Numeric(10, 0), default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("branch_id", "source_code", name="uq_counter_branch_source"),
    )


class CustomerHourBalance(Base):
    """ยอดคงเหลือชั่วโมงของลูกค้าแต่ละคน — มี 1 แถวต่อลูกค้า"""
    __tablename__ = "customer_hour_balances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, unique=True)
    remaining: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    # last_updated_by: user ที่อัปเดตล่าสุด (ใช้ตรวจสอบ audit)
    last_updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
