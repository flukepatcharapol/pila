"""
api/migrations/env.py

Alembic environment configuration
ต้อง import ทุก model ก่อน run_migrations เพื่อให้ Base.metadata รู้จัก table ทั้งหมด
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# เพิ่ม backend/api ใน path เพื่อ import api package ได้
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.database import Base
# import ทุก model เพื่อให้ Base.metadata รู้จัก — ถ้าขาดตัวไหน table นั้นจะไม่ถูก migrate
from api.models import (
    Partner, Branch,
    User, SourceType, UserRole, LoginAttempt, PinAttempt, PinOtp, PasswordResetToken, UserSession,
    Customer, CustomerHourBalance, CustomerCodeCounter, CustomerHourLog,
    Trainer, Caretaker,
    Package, PackageBranchScope,
    Order, OrderPayment,
    Booking, CancelPolicy,
    PermissionMatrix, FeatureToggle,
    ActivityLog,
    GoogleToken, SignaturePrintFile, UserPreference,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# อ่าน DATABASE_URL จาก environment variable (ใช้ใน Docker / CI)
db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Offline mode: สร้าง SQL script โดยไม่ต้องเชื่อม DB จริง
    ใช้สำหรับ generate migration script
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online mode: เชื่อม DB จริงแล้ว run migrations
    ใช้ใน production deployment
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
