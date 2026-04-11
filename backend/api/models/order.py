import uuid
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Numeric, Boolean, Date, DateTime, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    package_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("packages.id"), nullable=True)
    trainer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trainers.id"), nullable=True)
    caretaker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("caretakers.id"), nullable=True)
    # created_by: user ที่สร้าง order (สำหรับ audit + activity log)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[int] = mapped_column(Numeric(10, 0), default=0, nullable=False)
    bonus_hours: Mapped[int] = mapped_column(Numeric(10, 0), default=0, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    price_per_session: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    is_renewal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # renewed_from_id: ลิงก์ไปยัง order เดิมถ้าเป็น renewal
    renewed_from_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes2: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class OrderPayment(Base):
    """บันทึกการชำระเงินแต่ละงวดของ order (installment payment tracking)"""
    __tablename__ = "order_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # recorded_by: user ที่บันทึกการชำระ
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
