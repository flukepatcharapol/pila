from pydoc import text
import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text, UUID, Integer, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base

if TYPE_CHECKING:
    from api.models.branch import Branch


class UserRole(str, enum.Enum):
    DEVELOPER = "DEVELOPER"
    OWNER = "OWNER"
    BRANCH_MASTER = "BRANCH_MASTER"
    ADMIN = "ADMIN"
    TRAINER = "TRAINER"


# Association table: user ↔ branch (many-to-many)
# Replaces the old single-branch User.branch_id column.
user_branches = Table(
    "user_branches",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("branch_id", UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True),
)


class SourceType(Base):
    __tablename__ = "source_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pin_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Multi-branch membership. Empty list for DEVELOPER/OWNER (unrestricted).
    branches: Mapped[list["Branch"]] = relationship(
        "Branch", secondary=user_branches, lazy="selectin"
    )


class LoginAttempt(Base):
    """ติดตาม failed login attempts เพื่อ brute force protection"""
    __tablename__ = "login_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PinAttempt(Base):
    """ติดตาม failed PIN attempts เพื่อ lockout protection"""
    __tablename__ = "pin_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PinOtp(Base):
    """OTP สำหรับ PIN reset ผ่าน email"""
    __tablename__ = "pin_otps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class PasswordResetToken(Base):
    """Token สำหรับ password reset ผ่าน email"""
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class UserSession(Base):
    """เก็บ active sessions เพื่อ logout / token invalidation"""
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_jti: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)


class PasswordSession(Base):
    """Opaque password session — issued after login, used to obtain access JWT via PIN verify.
    Approach B: token is stored as SHA-256 hash only; raw token returned to client once.
    """
    __tablename__ = "password_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
