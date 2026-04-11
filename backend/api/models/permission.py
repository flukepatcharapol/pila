import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class PermissionMatrix(Base):
    """Permission matrix ต่อ role/feature_name/action — ควบคุม CRUD ของแต่ละ role"""
    __tablename__ = "permission_matrix"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # branch_id: NULL=ใช้กับทุก branch (owner level), ไม่ NULL=เฉพาะ branch นั้น
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # feature_name: ชื่อ module เช่น 'customer', 'order', 'booking' (เดิม: resource/module)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # action: VIEW|CREATE|EDIT|DELETE
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    # is_allowed: True=อนุญาต (เดิมชื่อ allowed)
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("branch_id", "role", "feature_name", "action", name="uq_permission"),
    )


class FeatureToggle(Base):
    """สวิตช์เปิด/ปิด feature ต่อ partner — ปิดแล้ว API ทุก endpoint ของ module นั้น reject 403"""
    __tablename__ = "feature_toggles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    # feature_name: ชื่อ feature เช่น 'booking', 'tax_accounting' (เดิม: module)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("partner_id", "feature_name", name="uq_feature_toggle"),
    )
