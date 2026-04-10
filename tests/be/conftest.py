# tests/be/conftest.py  (วางที่ tests/be/)
#
# BE-specific fixtures สำหรับ pytest + httpx API tests
# pytest โหลดไฟล์นี้อัตโนมัติก่อนทุก test ใน tests/be/
# เหตุผล: แยก database + auth fixtures ออกจาก FE browser fixtures

import pytest
import asyncio
from datetime import date
from httpx import AsyncClient
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
    create_jwt_token,       # สร้าง JWT token สำหรับ test
)
from api.services.customer import generate_customer_code


# ─── Database Engine ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """
    สร้าง SQLAlchemy engine เชื่อมกับ test database
    scope="session" = สร้างครั้งเดียวต่อการรัน pytest ทั้งหมด (ประหยัด connection overhead)

    ใช้ database แยก (studio_test) ไม่กระทบ development database
    """
    # สร้าง engine จาก TEST_DATABASE_URL ใน .env.test
    engine = create_engine(settings.TEST_DATABASE_URL)

    # สร้าง tables ทั้งหมดตาม models (idempotent — safe ถ้ามีอยู่แล้ว)
    Base.metadata.create_all(bind=engine)

    yield engine  # ส่ง engine ให้ fixtures อื่นใช้

    # หลัง session ทั้งหมดเสร็จ → drop tables เพื่อ clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    สร้าง database session สำหรับแต่ละ test function
    scope="function" = rollback ทุกอย่างหลัง test จบ → tests แยกจากกัน 100%

    ทำไม rollback ไม่ใช่ delete:
    - rollback เร็วกว่า
    - ไม่มี orphaned data
    - ไม่กระทบ tests อื่น
    """
    # เปิด connection และเริ่ม transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # สร้าง session จาก connection เดิม (nested transaction)
    TestSession = sessionmaker(bind=connection)
    session = TestSession()

    yield session  # ส่ง session ให้ test ใช้

    # Teardown: ปิด session แล้ว rollback transaction ทั้งหมด
    session.close()
    transaction.rollback()   # ยกเลิกทุกการเปลี่ยนแปลงใน test นี้
    connection.close()


@pytest.fixture(scope="function")
async def client(db_session):
    """
    สร้าง httpx AsyncClient สำหรับยิง API requests ใน test
    Override get_db dependency ให้ใช้ test session แทน production session
    ทำให้ API ใช้ DB เดียวกับที่ test กำลัง control และ rollback ได้

    ใช้ AsyncClient in-process (ไม่ต้องรัน server จริง) → test เร็วขึ้นมาก
    """
    def override_get_db():
        # คืน test session แทน production session
        yield db_session

    # แทนที่ get_db dependency ด้วย test version
    app.dependency_overrides[get_db] = override_get_db

    # สร้าง async HTTP client ที่ยิงตรงไปยัง FastAPI app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # ล้าง override หลัง test เสร็จ
    app.dependency_overrides.clear()


# ─── Seed Data ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def seed_data(test_engine):
    """
    สร้างข้อมูลพื้นฐานที่ทุก test ต้องการ
    scope="session" = สร้างครั้งเดียว share ทั้ง session (ประหยัดเวลา)

    Structure:
    - 1 partner: Test Partner
    - 3 branches: Pattaya (BPY), Chachoengsao (BCC), Kanchanaburi (BKB)
    - source types: MKT (Page), PAT (Walk In) ต่อสาขา
    - 1 user ต่อ role: developer, owner, branch_master (Pattaya), admin, trainer
    """
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()

    # ─── Partner ─────────────────────────────────────────────────────────────────

    partner = Partner(
        name="Test Partner",
        is_active=True,
    )
    session.add(partner)
    session.flush()  # flush เพื่อให้ได้ partner.id ก่อน commit

    # ─── Branches ────────────────────────────────────────────────────────────────

    pattaya = Branch(
        partner_id=partner.id,
        name="Pattaya",
        prefix="BPY",
        opening_time="09:00",
        closing_time="21:00",
        is_active=True,
    )
    chachoengsao = Branch(
        partner_id=partner.id,
        name="Chachoengsao",
        prefix="BCC",
        opening_time="09:00",
        closing_time="21:00",
        is_active=True,
    )
    kanchanaburi = Branch(
        partner_id=partner.id,
        name="Kanchanaburi",
        prefix="BKB",
        opening_time="09:00",
        closing_time="21:00",
        is_active=True,
    )
    session.add_all([pattaya, chachoengsao, kanchanaburi])
    session.flush()

    branches = [pattaya, chachoengsao, kanchanaburi]

    # ─── Source Types (ต่อสาขา) ──────────────────────────────────────────────────

    for branch in branches:
        session.add_all([
            SourceType(branch_id=branch.id, label="Page",    code="MKT"),
            SourceType(branch_id=branch.id, label="Walk In", code="PAT"),
        ])
    session.flush()

    # ─── Users (1 ต่อ role) ──────────────────────────────────────────────────────

    hashed_password = hash_password("test_pass")  # hash ครั้งเดียว ใช้ซ้ำ

    developer = User(
        partner_id=partner.id,
        username="developer",
        email="developer@test.com",
        password_hash=hashed_password,
        role="DEVELOPER",
        is_active=True,
    )
    owner = User(
        partner_id=partner.id,
        username="owner",
        email="owner@test.com",
        password_hash=hashed_password,
        role="OWNER",
        is_active=True,
    )
    branch_master = User(
        partner_id=partner.id,
        branch_id=pattaya.id,       # assigned to Pattaya
        username="bm_pattaya",
        email="bm_pattaya@test.com",
        password_hash=hashed_password,
        role="BRANCH_MASTER",
        is_active=True,
    )
    admin = User(
        partner_id=partner.id,
        branch_id=pattaya.id,       # assigned to Pattaya
        username="admin",
        email="admin@test.com",
        password_hash=hashed_password,
        role="ADMIN",
        is_active=True,
    )
    trainer_user = User(
        partner_id=partner.id,
        branch_id=pattaya.id,       # assigned to Pattaya
        username="trainer",
        email="trainer@test.com",
        password_hash=hashed_password,
        role="TRAINER",
        is_active=True,
    )
    session.add_all([developer, owner, branch_master, admin, trainer_user])
    session.commit()

    yield {
        "partner": partner,
        "branches": branches,
        "pattaya": pattaya,
        "chachoengsao": chachoengsao,
        "kanchanaburi": kanchanaburi,
        "users": {
            "developer":    developer,
            "owner":        owner,
            "branch_master": branch_master,
            "admin":        admin,
            "trainer":      trainer_user,
        },
    }

    session.close()


# ─── Auth Token Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def auth_token(seed_data):
    """
    Factory fixture: รับ role string แล้วคืน JWT token ที่ผ่าน PIN แล้ว
    พร้อมใช้งานทุก protected API endpoint

    ใช้งาน:
        token = auth_token("admin")
        res = await client.get("/customers", headers={"Authorization": f"Bearer {token}"})
    """
    def _get_token(role: str) -> str:
        # ดึง user object ของ role นั้น
        user = seed_data["users"][role]

        # สร้าง JWT token พร้อม pin_verified=True (ข้าม PIN flow ใน test)
        return create_jwt_token(
            user_id=str(user.id),
            role=user.role,
            branch_id=str(user.branch_id) if user.branch_id else None,
            partner_id=str(user.partner_id),
            pin_verified=True,              # ผ่าน PIN แล้ว
        )
    return _get_token


# สร้าง shortcut fixtures สำหรับแต่ละ role
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
    ใช้: customer_id = create_customer(branch="pattaya", source="MKT")
    """
    def _create(branch: str = "pattaya",
                source_code: str = "MKT",
                status: str = "ACTIVE",
                **kwargs) -> str:
        # หา branch object จาก name
        branch_obj = next(
            b for b in seed_data["branches"]
            if b.name.lower() == branch.lower()
        )
        # หา source type จาก branch + code
        source_type = db_session.query(SourceType).filter_by(
            branch_id=branch_obj.id, code=source_code
        ).first()

        # สร้าง customer code อัตโนมัติ (เดียวกับ production logic)
        code = generate_customer_code(
            branch_prefix=branch_obj.prefix,
            source_code=source_code,
            db=db_session,
        )

        customer = Customer(
            partner_id=branch_obj.partner_id,
            branch_id=branch_obj.id,
            source_type_id=source_type.id,
            customer_code=code,
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "Customer"),
            nickname=kwargs.get("nickname", "TestNick"),
            status=status,
        )
        db_session.add(customer)
        db_session.flush()

        # สร้าง hour balance เริ่มต้น = 0
        db_session.add(CustomerHourBalance(
            customer_id=customer.id,
            remaining=kwargs.get("initial_hours", 0),
        ))
        db_session.flush()

        return str(customer.id)
    return _create


@pytest.fixture
def create_trainer(db_session, seed_data):
    """Factory: สร้าง test trainer แล้วคืน trainer_id"""
    def _create(branch: str = "pattaya", status: str = "ACTIVE", **kwargs) -> str:
        branch_obj = next(
            b for b in seed_data["branches"]
            if b.name.lower() == branch.lower()
        )
        trainer = Trainer(
            branch_id=branch_obj.id,
            name=kwargs.get("name", "Test Trainer"),
            nickname=kwargs.get("nickname", "T"),
            status=status,
        )
        db_session.add(trainer)
        db_session.flush()
        return str(trainer.id)
    return _create


@pytest.fixture
def create_package(db_session, seed_data):
    """Factory: สร้าง test package แล้วคืน package_id"""
    def _create(branch_scope: str = "ALL",
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
        )
        db_session.add(package)
        db_session.flush()
        return str(package.id)
    return _create


@pytest.fixture
def create_order(db_session, seed_data, create_customer, create_package):
    """
    Factory: สร้าง test order แล้วคืน order_id (พร้อม allocate hours ให้ customer)
    ใช้: order_id = create_order(hours=10)
    """
    def _create(hours: int = 10,
                bonus_hours: int = 0,
                payment_method: str = "BANK_TRANSFER",
                **kwargs) -> str:
        # สร้าง customer และ package ถ้าไม่ได้ระบุมา
        customer_id = kwargs.get("customer_id") or create_customer()
        package_id  = kwargs.get("package_id")  or create_package()
        branch_id   = str(seed_data["pattaya"].id)

        order = Order(
            partner_id=seed_data["partner"].id,
            branch_id=branch_id,
            customer_id=customer_id,
            package_id=package_id,
            order_date=date.today(),
            hours=hours,
            bonus_hours=bonus_hours,
            payment_method=payment_method,
            total_price=kwargs.get("total_price", 5000.0),
            paid_amount=kwargs.get("paid_amount", 5000.0),
        )
        db_session.add(order)
        db_session.flush()

        # อัปเดต hour balance ของ customer
        balance = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).with_for_update().first()

        if balance:
            balance.remaining += (hours + bonus_hours)  # เพิ่ม hours จาก order
        db_session.flush()

        return str(order.id)
    return _create


# ─── Allure Auto-Metadata ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def allure_be_metadata(request):
    """
    autouse=True = ทำงานทุก BE test อัตโนมัติ
    ติด Allure labels สำหรับ report grouping
    """
    # ดึงชื่อ module เช่น test_customer_api → Customer Api
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
