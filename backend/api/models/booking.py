import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, Boolean, UUID, Integer
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    trainer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trainers.id"), nullable=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    caretaker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("caretakers.id"), nullable=True)
    # booking_type: CUSTOMER=นัดลูกค้า, STAFF_SCHEDULE=ตารางงาน trainer
    booking_type: Mapped[str] = mapped_column(String(20), default="CUSTOMER", nullable=False)
    # booking_source: INTERNAL=สร้างใน app, EXTERNAL_API=สร้างจาก customer product
    booking_source: Mapped[str] = mapped_column(String(20), default="INTERNAL", nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # status: PENDING=รอยืนยัน, CONFIRMED=ยืนยันแล้ว, CANCELLED=ยกเลิก
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # line_notified: True เมื่อส่ง LINE notification ไปแล้ว
    line_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # hour_returned: True เมื่อคืนชั่วโมงให้ลูกค้าแล้ว (เมื่อ cancel + return_hour=True)
    hour_returned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CancelPolicy(Base):
    """นโยบายยกเลิก booking ต่อ branch — มี 1 แถวต่อ branch"""
    __tablename__ = "cancel_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # branch_id: unique เพราะแต่ละ branch มี policy ได้แค่ 1 ชุด
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, unique=True)
    # hours_before: ต้องยกเลิกก่อนกี่ชั่วโมง
    hours_before: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    # return_hour: True=คืนชั่วโมงให้ลูกค้าเมื่อ cancel
    return_hour: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
