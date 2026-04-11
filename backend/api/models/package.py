import uuid
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Numeric, Boolean, Date, DateTime, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # sale_type: SALE=ขายปกติ, PRE_SALE=ขายก่อนกำหนด (ปิดกั้นจาก order form)
    sale_type: Mapped[str] = mapped_column(String(20), default="SALE", nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # branch_scope: ALL=ทุก branch, SELECTED=เฉพาะ branch ที่กำหนดใน package_branch_scopes, SPECIFIC=branch เดียว
    branch_scope: Mapped[str] = mapped_column(String(10), default="ALL", nullable=False)
    # branch_id: ใช้เมื่อ branch_scope = SPECIFIC (ผูกกับ branch เดียว)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    active_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PackageBranchScope(Base):
    """กำหนด branch ที่ package ใช้ได้ — ใช้เฉพาะเมื่อ package.branch_scope = 'SELECTED'"""
    __tablename__ = "package_branch_scopes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("packages.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("package_id", "branch_id", name="uq_pkg_branch"),
    )
