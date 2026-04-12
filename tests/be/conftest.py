# tests/be/conftest.py  (วางที่ tests/be/)
#
# BE-specific fixtures สำหรับ pytest + httpx API tests
# pytest โหลดไฟล์นี้อัตโนมัติก่อนทุก test ใน tests/be/
# เหตุผล: แยก database + auth fixtures ออกจาก FE browser fixtures

import uuid
import pytest
from datetime import date, datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import allure

from api.main import app                    # FastAPI app instance
from api.database import Base, get_db       # SQLAlchemy base + dependency
from api.models import (                    # import all models ให้ Base รู้จัก
    Partner, Branch, User, SourceType,
    Customer, CustomerHourBalance,
    Trainer, Caretaker, Package, Order,
    Booking,
)
from api.config import settings             # app settings (TEST_DATABASE_URL ฯลฯ)
from api.utils.auth import (
    hash_password,          # hash password ก่อน store ใน DB
    hash_pin,               # hash PIN ก่อน store ใน DB
    create_jwt_token,       # สร้าง JWT token สำหรับ test
)
from api.services.customer import generate_customer_code


# ─── Database Engine ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """
    สร้าง SQLAlchemy engine เชื่อมกับ test database
    scope="session" = สร้างครั้งเดียวต่อการรัน pytest ทั้งหมด
    """
    engine = create_engine(settings.TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    สร้าง database session สำหรับแต่ละ test function
    scope="function" = rollback ทุกอย่างหลัง test จบ → tests แยกจากกัน 100%
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    test_session_factory = sessionmaker(bind=connection)
    session = test_session_factory()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
async def client(db_session):
    """
    สร้าง httpx AsyncClient สำหรับยิง API requests ใน test
    Override get_db dependency ให้ใช้ test session แทน production session
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()


# ─── Seed Data ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def seed_data(test_engine):
    """
    สร้างข้อมูลพื้นฐานที่ทุก test ต้องการ
    scope="session" = สร้างครั้งเดียว share ทั้ง session

    Structure:
    - 1 partner: Test Partner
    - 3 branches: Pattaya (BPY), Chachoengsao (BCC), Kanchanaburi (BKB)
    - source types: MKT (Page), PAT (Walk In) ต่อสาขา
    - 1 user ต่อ role: developer, owner, branch_master (Pattaya), admin, trainer
    """
    test_session_factory = sessionmaker(bind=test_engine)
    session = test_session_factory()

    # ─── Partner ─────────────────────────────────────────────────────────────────

    partner = Partner(name="Test Partner", is_active=True)
    session.add(partner)
    session.flush()

    # ─── Branches ────────────────────────────────────────────────────────────────

    pattaya = Branch(
        partner_id=partner.id, name="Pattaya", prefix="BPY",
        opening_time="09:00", closing_time="21:00", is_active=True,
    )
    chachoengsao = Branch(
        partner_id=partner.id, name="Chachoengsao", prefix="BCC",
        opening_time="09:00", closing_time="21:00", is_active=True,
    )
    kanchanaburi = Branch(
        partner_id=partner.id, name="Kanchanaburi", prefix="BKB",
        opening_time="09:00", closing_time="21:00", is_active=True,
    )
    session.add_all([pattaya, chachoengsao, kanchanaburi])
    session.flush()

    branch_list = [pattaya, chachoengsao, kanchanaburi]

    # ─── Source Types (ต่อสาขา) ──────────────────────────────────────────────────

    source_type_map = {}
    for branch_record in branch_list:
        mkt_source = SourceType(branch_id=branch_record.id, label="Page",    code="MKT")
        pat_source = SourceType(branch_id=branch_record.id, label="Walk In", code="PAT")
        session.add_all([mkt_source, pat_source])
        session.flush()
        prefix = branch_record.prefix  # BPY, BCC, BKB
        source_type_map[f"{prefix}_MKT"] = mkt_source
        source_type_map[f"{prefix}_PAT"] = pat_source

    # ─── Users (1 ต่อ role) ──────────────────────────────────────────────────────

    hashed_password = hash_password("test_pass")
    hashed_pin = hash_pin("123456")

    developer = User(
        partner_id=partner.id,
        username="developer", email="developer@test.com",
        password_hash=hashed_password, pin_hash=hashed_pin, role="DEVELOPER", is_active=True,
    )
    owner = User(
        partner_id=partner.id,
        username="owner", email="owner@test.com",
        password_hash=hashed_password, pin_hash=hashed_pin, role="OWNER", is_active=True,
    )
    branch_master = User(
        partner_id=partner.id, branch_id=pattaya.id,
        username="bm_pattaya", email="bm_pattaya@test.com",
        password_hash=hashed_password, pin_hash=hashed_pin, role="BRANCH_MASTER", is_active=True,
    )
    admin = User(
        partner_id=partner.id, branch_id=pattaya.id,
        username="admin", email="admin@test.com",
        password_hash=hashed_password, pin_hash=hashed_pin, role="ADMIN", is_active=True,
    )
    trainer_user = User(
        partner_id=partner.id, branch_id=pattaya.id,
        username="trainer", email="trainer@test.com",
        password_hash=hashed_password, pin_hash=hashed_pin, role="TRAINER", is_active=True,
    )
    session.add_all([developer, owner, branch_master, admin, trainer_user])
    session.commit()

    # ─── PinOtp (seed สำหรับ test_pin_reset_valid_otp) ───────────────────────────
    # สร้าง OTP record สำหรับ owner — ใช้ค่า "654321" (fixed test OTP)
    # expires far in the future เพื่อไม่หมดอายุระหว่าง test session
    from api.models.user import PinOtp as PinOtpModel
    pin_otp_seed = PinOtpModel(
        user_id=owner.id,
        otp_hash=hash_pin("654321"),
        expires_at=datetime.utcnow() + timedelta(days=365),
        used=False,
    )
    session.add(pin_otp_seed)
    session.commit()

    yield {
        "partner": partner,
        "branches": branch_list,
        "pattaya": pattaya,
        "chachoengsao": chachoengsao,
        "kanchanaburi": kanchanaburi,
        "source_types": source_type_map,  # e.g. {"BPY_MKT": <SourceType>, "BPY_PAT": ...}
        "users": {
            "developer":     developer,
            "owner":         owner,
            "branch_master": branch_master,
            "admin":         admin,
            "trainer":       trainer_user,
        },
    }

    session.close()


# ─── Auth Token Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def auth_token(seed_data):
    """
    Factory fixture: รับ role string แล้วคืน JWT token ที่ผ่าน PIN แล้ว
    พร้อมใช้งานทุก protected API endpoint
    """
    def _build_jwt_for_role(role: str) -> str:
        user_record = seed_data["users"][role]
        return create_jwt_token(
            user_id=str(user_record.id),
            role=user_record.role,
            branch_id=str(user_record.branch_id) if user_record.branch_id else None,
            partner_id=str(user_record.partner_id),
            pin_verified=True,
        )
    return _build_jwt_for_role


@pytest.fixture
def developer_token(auth_token):
    """JWT token สำหรับ developer — เข้าถึงได้ทุก partner/branch"""
    return auth_token("developer")

@pytest.fixture
def owner_token(auth_token):
    """JWT token สำหรับ owner — เข้าถึงได้ทุก branch ใน partner"""
    return auth_token("owner")

@pytest.fixture
def branch_master_token(auth_token):
    """JWT token สำหรับ branch_master (Pattaya) — เข้าถึงได้เฉพาะ Pattaya"""
    return auth_token("branch_master")

@pytest.fixture
def admin_token(auth_token):
    """JWT token สำหรับ admin (Pattaya) — permission matrix gated"""
    return auth_token("admin")

@pytest.fixture
def trainer_token(auth_token):
    """JWT token สำหรับ trainer (Pattaya) — permission matrix gated"""
    return auth_token("trainer")


# ─── Factory Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def create_customer(db_session, seed_data):
    """
    Factory: สร้าง test customer แล้วคืน customer_id (string UUID)
    ใช้: customer_id = create_customer(branch="pattaya", source_code="MKT")
    """
    def _build_customer(branch: str = "pattaya",
                        source_code: str = "MKT",
                        status: str = "ACTIVE",
                        **kwargs) -> str:
        target_branch = next(
            branch_record for branch_record in seed_data["branches"]
            if branch_record.name.lower() == branch.lower()
        )
        source_type = db_session.query(SourceType).filter_by(
            branch_id=target_branch.id, code=source_code
        ).first()

        customer_code = generate_customer_code(
            branch_prefix=target_branch.prefix,
            source_code=source_code,
            db=db_session,
        )

        customer = Customer(
            partner_id=target_branch.partner_id,
            branch_id=target_branch.id,
            source_type_id=source_type.id,
            customer_code=customer_code,
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "Customer"),
            nickname=kwargs.get("nickname", "TestNick"),
            status=status,
        )
        db_session.add(customer)
        db_session.flush()

        db_session.add(CustomerHourBalance(
            customer_id=customer.id,
            remaining=kwargs.get("initial_hours", 0),
        ))
        db_session.flush()

        # สร้าง activity log เพื่อให้ GET /activity-log มี entries ให้ query
        from api.models.activity_log import ActivityLog as _ActivityLog
        db_session.add(_ActivityLog(
            action="customer.create",
            target_type="customer",
            target_id=str(customer.id),
            branch_id=target_branch.id,
            partner_id=target_branch.partner_id,
        ))
        db_session.flush()

        return str(customer.id)
    return _build_customer


@pytest.fixture
def create_trainer(db_session, seed_data):
    """Factory: สร้าง test trainer แล้วคืน trainer_id"""
    def _build_trainer(branch: str = "pattaya", status: str = "ACTIVE", **kwargs) -> str:
        target_branch = next(
            branch_record for branch_record in seed_data["branches"]
            if branch_record.name.lower() == branch.lower()
        )
        trainer = Trainer(
            branch_id=target_branch.id,
            name=kwargs.get("name", "Test Trainer"),
            nickname=kwargs.get("nickname", "T"),
            status=status,
        )
        db_session.add(trainer)
        db_session.flush()
        return str(trainer.id)
    return _build_trainer


@pytest.fixture
def create_package(db_session, seed_data):
    """Factory: สร้าง test package แล้วคืน package_id"""
    def _build_package(branch_scope: str = "ALL",
                       hours: int = 10,
                       price: float = 5000.0,
                       is_active: bool = True,
                       **kwargs) -> str:
        package = Package(
            partner_id=seed_data["partner"].id,
            name=kwargs.get("name", "Test Package"),
            hours=hours,
            sale_type=kwargs.get("sale_type", "SALE"),
            price=price,
            branch_scope=branch_scope,
            is_active=is_active,
            active_from=kwargs.get("active_from", date.today() - timedelta(days=30)),
            active_until=kwargs.get("active_until", date.today() + timedelta(days=365)),
        )
        db_session.add(package)
        db_session.flush()
        return str(package.id)
    return _build_package


@pytest.fixture
def create_order(db_session, seed_data, create_customer, create_package):
    """
    Factory: สร้าง test order แล้วคืน order_id (พร้อม allocate hours ให้ customer)
    ใช้: order_id = create_order(hours=10)
    """
    def _build_order(hours: int = 10,
                     bonus_hours: int = 0,
                     payment_method: str = "BANK_TRANSFER",
                     **kwargs) -> str:
        customer_id = kwargs.get("customer_id") or create_customer()
        package_id  = kwargs.get("package_id")  or create_package()
        branch_id   = seed_data["pattaya"].id

        order = Order(
            partner_id=seed_data["partner"].id,
            branch_id=branch_id,
            customer_id=uuid.UUID(str(customer_id)),
            package_id=uuid.UUID(str(package_id)),
            order_date=date.today(),
            hours=hours,
            bonus_hours=bonus_hours,
            payment_method=payment_method,
            total_price=kwargs.get("total_price", 5000.0),
            paid_amount=kwargs.get("paid_amount", 5000.0),
        )
        db_session.add(order)
        db_session.flush()

        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=uuid.UUID(str(customer_id))
        ).with_for_update().first()

        if hour_balance_record:
            hour_balance_record.remaining += (hours + bonus_hours)
        db_session.flush()

        return str(order.id)
    return _build_order


@pytest.fixture
def create_caretaker(db_session, seed_data):
    """Factory: สร้าง test caretaker แล้วคืน caretaker_id"""
    def _build_caretaker(branch: str = "pattaya", status: str = "ACTIVE", **kwargs) -> str:
        target_branch = next(
            branch_record for branch_record in seed_data["branches"]
            if branch_record.name.lower() == branch.lower()
        )
        caretaker = Caretaker(
            branch_id=target_branch.id,
            name=kwargs.get("name", "Test Caretaker"),
            email=kwargs.get("email", "caretaker@test.com"),
            status=status,
        )
        db_session.add(caretaker)
        db_session.flush()
        return str(caretaker.id)
    return _build_caretaker


@pytest.fixture
def create_user(db_session, seed_data):
    """
    Factory: สร้าง test user ด้วย role ที่กำหนด แล้วคืน user_id
    ใช้: user_id = create_user(role="ADMIN", branch="pattaya")
    """
    def _build_user(role: str = "ADMIN", branch: str = "pattaya", **kwargs) -> str:
        target_branch = next(
            (branch_record for branch_record in seed_data["branches"]
             if branch_record.name.lower() == branch.lower()),
            None,
        )
        unique_suffix = str(id(kwargs))
        new_user = User(
            partner_id=seed_data["partner"].id,
            branch_id=target_branch.id if target_branch else None,
            username=kwargs.get("username", f"test_{role.lower()}_{unique_suffix}"),
            email=kwargs.get("email", f"test_{role.lower()}_{unique_suffix}@test.com"),
            password_hash=hash_password(kwargs.get("password", "test_pass")),
            role=role,
            is_active=True,
        )
        db_session.add(new_user)
        db_session.flush()
        return str(new_user.id)
    return _build_user


@pytest.fixture
def create_booking(db_session, seed_data, create_customer, create_trainer):
    """
    Factory: สร้าง test booking แล้วคืน booking_id
    ใช้: booking_id = create_booking(status="confirmed", trainer_id=trainer_id)
    """
    def _build_booking(status: str = "pending",
                       trainer_id: str = None,
                       customer_id: str = None,
                       **kwargs) -> str:
        resolved_trainer_id = trainer_id or create_trainer(branch="pattaya")
        resolved_customer_id = customer_id or create_customer(branch="pattaya")
        booking_date = kwargs.get("booking_date", date.today())

        booking = Booking(
            branch_id=seed_data["pattaya"].id,
            trainer_id=uuid.UUID(str(resolved_trainer_id)),
            customer_id=uuid.UUID(str(resolved_customer_id)),
            start_time=kwargs.get("start_time", f"{booking_date}T09:00:00"),
            end_time=kwargs.get("end_time", f"{booking_date}T10:00:00"),
            booking_type=kwargs.get("booking_type", "CUSTOMER"),
            status=status,
        )
        db_session.add(booking)
        db_session.flush()
        return str(booking.id)
    return _build_booking


@pytest.fixture
def confirmed_booking(create_booking):
    """Convenience: booking ที่ status=confirmed พร้อมใช้ใน tests"""
    return create_booking(status="confirmed")


@pytest.fixture
def customer_with_balance(create_customer):
    """
    Factory: สร้าง customer ที่มี hour_balance ตามที่กำหนด
    ใช้ใน HOUR tests ที่ต้องการ customer ที่มี/ไม่มี hours เหลือ

    ใช้งาน:
        customer_id = customer_with_balance(hours=5)
        customer_id = customer_with_balance(hours=0)
    """
    def _build_customer_with_balance(hours: int = 5, branch: str = "pattaya") -> str:
        return create_customer(branch=branch, initial_hours=hours)
    return _build_customer_with_balance


@pytest.fixture
def expired_package(create_package):
    """Convenience: package ที่หมดอายุแล้ว (active_until = เมื่อวาน)"""
    return create_package(
        active_until=date.today() - timedelta(days=1),
    )


@pytest.fixture
def future_package(create_package):
    """Convenience: package ที่ยังไม่เริ่ม (active_from = พรุ่งนี้)"""
    return create_package(
        active_from=date.today() + timedelta(days=1),
        active_until=date.today() + timedelta(days=365),
    )


@pytest.fixture
def permission_override(db_session):
    """
    Factory: เปิด/ปิด permission ใน matrix แล้วคืนค่าเดิมหลัง test
    ใช้ใน tests ที่ต้องการ simulate permission ที่ถูก disable

    ใช้งาน:
        permission_override("admin", "booking", "view", False)
    """
    from api.models.permission import PermissionMatrix

    # Each entry: (record, original_value, is_new_record)
    applied_changes = []

    def _apply_permission_override(role: str, resource: str, action: str, is_allowed: bool):
        permission_record = db_session.query(PermissionMatrix).filter_by(
            role=role.upper(), feature_name=resource, action=action.upper()
        ).first()
        if permission_record:
            original_value = permission_record.is_allowed
            applied_changes.append((permission_record, original_value, False))
            permission_record.is_allowed = is_allowed
            db_session.flush()
        else:
            # Create new record to override
            permission_record = PermissionMatrix(
                role=role.upper(),
                feature_name=resource,
                action=action.upper(),
                is_allowed=is_allowed,
            )
            db_session.add(permission_record)
            db_session.flush()
            applied_changes.append((permission_record, None, True))

    yield _apply_permission_override

    for permission_record, original_value, is_new in reversed(applied_changes):
        if is_new:
            db_session.delete(permission_record)
        else:
            permission_record.is_allowed = original_value
    db_session.flush()


# ─── Allure Auto-Metadata ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def allure_be_metadata(request):
    """
    autouse=True = ทำงานทุก BE test อัตโนมัติ
    ติด Allure labels สำหรับ report grouping
    """
    module_name = (
        request.node.module.__name__
        .replace("test_", "")
        .replace("_api", "")
        .replace("_", " ")
        .title()
    )
    allure.dynamic.feature(f"BE API: {module_name}")
    allure.dynamic.story(request.node.name)
    allure.dynamic.tag("be", "api", "pytest")
