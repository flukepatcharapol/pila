"""001_initial_schema

Create all tables for Pila Studio Management

Revision ID: 001
Revises:
Create Date: 2026-04-11

หมายเหตุ: migration นี้ใช้ Alembic autogenerate format
ในการ deploy ครั้งแรกให้รัน: alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    สร้าง tables ทั้งหมดตาม model definitions
    เรียงตาม dependency order:
    1. ไม่มี FK dependency (partners)
    2. FK ไป partners (branches, users)
    3. FK ไป branches + users (customers, trainers, packages, ...)
    4. FK ไปทุกอย่าง (orders, bookings, logs, ...)
    """
    # 1. partners
    op.create_table(
        "partners",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # 2. branches
    op.create_table(
        "branches",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", sa.UUID(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("prefix", sa.String(10), nullable=False, unique=True),
        sa.Column("opening_time", sa.String(10)),
        sa.Column("closing_time", sa.String(10)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # 3. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", sa.UUID(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id")),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("pin_hash", sa.String(255)),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("pin_locked", sa.Boolean, default=False),
        sa.Column("pin_attempts", sa.Integer, default=0),
        sa.Column("last_login_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # 4. source_types
    op.create_table(
        "source_types",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("branch_id", "code", name="uq_source_type_branch_code"),
    )

    # 5. auth tables
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("success", sa.Boolean, default=False),
        sa.Column("attempted_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "pin_attempts",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("success", sa.Boolean, default=False),
        sa.Column("attempted_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "pin_otps",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("otp_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("request_count", sa.Integer, default=1),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_jti", sa.String(255), unique=True),
        sa.Column("access_token", sa.Text),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # 6. trainers + caretakers (ต้องมาก่อน customers)
    op.create_table(
        "trainers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(100)),
        sa.Column("display_name", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("profile_photo_url", sa.String(500)),
        sa.Column("status", sa.String(20), default="ACTIVE"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "caretakers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("status", sa.String(20), default="ACTIVE"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # 7. customers
    op.create_table(
        "customers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", sa.UUID(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("source_type_id", sa.UUID(), sa.ForeignKey("source_types.id")),
        sa.Column("trainer_id", sa.UUID(), sa.ForeignKey("trainers.id")),
        sa.Column("caretaker_id", sa.UUID(), sa.ForeignKey("caretakers.id")),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("customer_code", sa.String(50), unique=True, nullable=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255)),
        sa.Column("nickname", sa.String(100)),
        sa.Column("display_name", sa.String(255)),
        sa.Column("contact_channel", sa.String(20)),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("line_id", sa.String(100)),
        sa.Column("birthday", sa.Date),
        sa.Column("notes", sa.Text),
        sa.Column("profile_photo_url", sa.String(500)),
        sa.Column("is_duplicate", sa.Boolean, default=False),
        sa.Column("status", sa.String(20), default="ACTIVE"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "customer_code_counters",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("source_type_id", sa.UUID(), sa.ForeignKey("source_types.id")),
        sa.Column("source_code", sa.String(10), nullable=False),
        sa.Column("last_sequence", sa.Integer, default=0),
        sa.UniqueConstraint("branch_id", "source_code", name="uq_counter_branch_source"),
    )

    op.create_table(
        "customer_hour_balances",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id"), nullable=False, unique=True),
        sa.Column("remaining", sa.Numeric(10, 2), default=0),
        sa.Column("last_updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "customer_hour_logs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id")),
        sa.Column("trainer_id", sa.UUID(), sa.ForeignKey("trainers.id")),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("before_amount", sa.Integer, nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("after_amount", sa.Integer, nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # 8. packages
    op.create_table(
        "packages",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", sa.UUID(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("sale_type", sa.String(20), default="SALE"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("branch_scope", sa.String(10), default="ALL"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("active_from", sa.Date),
        sa.Column("active_until", sa.Date),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "package_branch_scopes",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("package_id", sa.UUID(), sa.ForeignKey("packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False),
        sa.UniqueConstraint("package_id", "branch_id", name="uq_pkg_branch"),
    )

    # 9. orders
    op.create_table(
        "orders",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", sa.UUID(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("package_id", sa.UUID(), sa.ForeignKey("packages.id")),
        sa.Column("trainer_id", sa.UUID(), sa.ForeignKey("trainers.id")),
        sa.Column("caretaker_id", sa.UUID(), sa.ForeignKey("caretakers.id")),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("order_date", sa.Date, nullable=False),
        sa.Column("hours", sa.Integer, default=0),
        sa.Column("bonus_hours", sa.Integer, default=0),
        sa.Column("payment_method", sa.String(30), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(12, 2), default=0),
        sa.Column("price_per_session", sa.Numeric(12, 2)),
        sa.Column("is_renewal", sa.Boolean, default=False),
        sa.Column("renewed_from_id", sa.UUID(), sa.ForeignKey("orders.id")),
        sa.Column("notes", sa.Text),
        sa.Column("notes2", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "order_payments",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", sa.UUID(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("paid_at", sa.Date, nullable=False),
        sa.Column("note", sa.Text),
        sa.Column("recorded_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # 10. bookings + cancel_policies
    op.create_table(
        "bookings",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False),
        sa.Column("trainer_id", sa.UUID(), sa.ForeignKey("trainers.id")),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id")),
        sa.Column("caretaker_id", sa.UUID(), sa.ForeignKey("caretakers.id")),
        sa.Column("booking_type", sa.String(20), default="CUSTOMER"),
        sa.Column("booking_source", sa.String(20), default="INTERNAL"),
        sa.Column("start_time", sa.DateTime, nullable=False),
        sa.Column("end_time", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), default="PENDING"),
        sa.Column("notes", sa.Text),
        sa.Column("line_notified", sa.Boolean, default=False),
        sa.Column("hour_returned", sa.Boolean, default=False),
        sa.Column("confirmed_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("confirmed_at", sa.DateTime),
        sa.Column("cancelled_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("cancelled_at", sa.DateTime),
        sa.Column("cancel_reason", sa.Text),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "cancel_policies",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id"), nullable=False, unique=True),
        sa.Column("hours_before", sa.Integer, default=24),
        sa.Column("return_hour", sa.Boolean, default=True),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # 11. permissions
    op.create_table(
        "permission_matrix",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id")),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("feature_name", sa.String(100), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("is_allowed", sa.Boolean, default=True),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("branch_id", "role", "feature_name", "action", name="uq_permission"),
    )

    op.create_table(
        "feature_toggles",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_id", sa.UUID(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("feature_name", sa.String(100), nullable=False),
        sa.Column("is_enabled", sa.Boolean, default=True),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("partner_id", "feature_name", name="uq_feature_toggle"),
    )

    # 12. activity_logs
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("partner_id", sa.UUID(), sa.ForeignKey("partners.id")),
        sa.Column("branch_id", sa.UUID(), sa.ForeignKey("branches.id")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50)),
        sa.Column("target_id", sa.String(50)),
        sa.Column("changes", sa.JSON),
        sa.Column("detail", sa.Text),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # 13. google integration + user preferences
    op.create_table(
        "google_tokens",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("connected_email", sa.String(255), nullable=False),
        sa.Column("access_token", sa.Text, nullable=False),
        sa.Column("refresh_token", sa.Text, nullable=False),
        sa.Column("token_expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "signature_print_files",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", sa.UUID(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("generated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("language", sa.String(5), default="TH"),
        sa.Column("dark_mode", sa.Boolean, default=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    """ลบ tables ทั้งหมด — เรียงย้อนกลับตาม FK dependency"""
    op.drop_table("user_preferences")
    op.drop_table("signature_print_files")
    op.drop_table("google_tokens")
    op.drop_table("activity_logs")
    op.drop_table("feature_toggles")
    op.drop_table("permission_matrix")
    op.drop_table("cancel_policies")
    op.drop_table("bookings")
    op.drop_table("order_payments")
    op.drop_table("orders")
    op.drop_table("package_branch_scopes")
    op.drop_table("packages")
    op.drop_table("customer_hour_logs")
    op.drop_table("customer_hour_balances")
    op.drop_table("customer_code_counters")
    op.drop_table("customers")
    op.drop_table("caretakers")
    op.drop_table("trainers")
    op.drop_table("user_sessions")
    op.drop_table("password_reset_tokens")
    op.drop_table("pin_otps")
    op.drop_table("pin_attempts")
    op.drop_table("login_attempts")
    op.drop_table("source_types")
    op.drop_table("users")
    op.drop_table("branches")
    op.drop_table("partners")
