"""
api/models/customer_hour.py

CustomerHourLog — บันทึกธุรกรรมชั่วโมงทุกครั้ง (เดิมชื่อ session_transaction_logs)
แยกออกมาจาก customer.py เพื่อให้ models แต่ละไฟล์มีหน้าที่ชัดเจน
"""
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, UUID, Integer
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class CustomerHourLog(Base):
    """
    บันทึกทุก transaction ที่เปลี่ยนแปลง hour balance ของลูกค้า
    transaction_type:
      PURCHASED   = ซื้อ package ใหม่ → hours เพิ่ม
      HOUR_DEDUCT = ใช้ชั่วโมง (1 ครั้งต่อการ deduct)
      HOUR_ADJUST = admin ปรับยอดมือ (+ หรือ -)
      NEW_CUSTOMER = ลูกค้าใหม่ (ชั่วโมงเริ่มต้น)
    """
    __tablename__ = "customer_hour_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    trainer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trainers.id"), nullable=True)
    # transaction_type: ประเภทธุรกรรม — ใช้ uppercase constant เสมอ
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # before_amount: ยอดก่อน transaction — ใช้ verify ความถูกต้อง
    before_amount: Mapped[float] = mapped_column(Integer, nullable=False)
    # amount: จำนวนที่เปลี่ยน (บวก=เพิ่ม, ลบ=หัก)
    amount: Mapped[float] = mapped_column(Integer, nullable=False)
    # after_amount: ยอดหลัง transaction (= before + amount)
    after_amount: Mapped[float] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # user_id: user ที่ทำ action (เดิมชื่อ actor_id — naming consistency)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
