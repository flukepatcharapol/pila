# Automation Test Plan — Studio Management
## Version 1.1 | 2026-04-08
### BE: pytest + httpx + Allure | FE: Playwright + pytest (Python) + Locator Fallback

---

## 1. Overview

| Layer | Framework | Runner | Config File |
|-------|-----------|--------|-------------|
| BE | pytest + httpx (async) + **Allure** | `pytest tests/be/` | `pytest.ini` |
| FE | Playwright + pytest + **Fallback Locator** | `pytest tests/fe/` | `pytest.ini` |
| Integration | pytest + httpx + Playwright | `pytest tests/integration/` | `pytest.ini` |

### Key Additions v1.1
- **BE:** Allure logging บันทึกทุก action, request/response, step ใน report
- **FE:** Locator fallback — primary `data-testid`, fallback XPath เมื่อ `STRICT_LOCATOR=false`

---

## 2. Full Folder Structure

```
tests/
├── pytest.ini                          # pytest global config (markers, paths, env)
├── conftest.py                         # Root conftest — shared across BE + FE + integration
├── .env.test                           # Test environment variables (STRICT_LOCATOR, etc.)
│
├── be/                                 # Backend API tests
│   ├── conftest.py                     # BE-specific fixtures (DB, tokens, factories, Allure)
│   ├── helpers/
│   │   ├── common_api.py              # Shared request helpers, assertion helpers, payload builders
│   │   └── allure_helper.py           # Allure logging helpers
│   ├── test_auth_api.py                # Auth endpoints (login→temp token, PIN→JWT, OTP, logout, internal)
│   ├── test_customer_api.py            # Customer CRUD + code generation + scoping
│   ├── test_order_api.py               # Order CRUD + payment tracking
│   ├── test_customer_hour_api.py       # Customer hour balance + log (เดิม: test_customer_hour_api.py)
│   ├── test_trainer_api.py             # Trainer CRUD + constraints
│   ├── test_caretaker_api.py           # Caretaker CRUD + branch scoping
│   ├── test_package_api.py             # Package CRUD + scope + active period
│   ├── test_booking_api.py             # Booking lifecycle + cancel policy + external API
│   ├── test_user_api.py                # User CRUD + role hierarchy
│   ├── test_permission_api.py          # Permission matrix + feature toggle (owner+)
│   ├── test_dashboard_api.py           # Dashboard per role
│   ├── test_activity_log_api.py        # Activity log entries + filters (branch_master+)
│   ├── test_branch_api.py              # Branch config + source types
│   ├── test_signature_print_api.py     # Google Drive integration
│   ├── test_settings_api.py            # User preferences + Google connect
│   ├── test_help_api.py                # Help manual + LINE QR
│   ├── test_security.py                # SQL injection, token isolation, rate limiting
│   ├── test_data_integrity.py          # FK constraints, negative balance, unique codes
│   └── test_input_validation.py        # Field validation across all endpoints
│
├── fe/                                 # Frontend Playwright tests
│   ├── conftest.py                     # FE-specific fixtures (browser, login helpers, fallback)
│   ├── helpers/
│   │   ├── common_web.py              # Shared web helpers (fill, click, login_as, asserts, mocks)
│   │   ├── locator.py                 # Fallback locator core (legacy — use common_web instead)
│   │   └── fallback_report.py         # Report ว่า test ไหน fallback ไปใช้ XPath
│   ├── test_auth.py                    # Login, PIN, forgot PIN/password, session expiry
│   ├── test_navigation.py              # Sidebar, role visibility, feature toggle overlay
│   ├── test_dashboard.py               # Dashboard per role, time filter, branch selector
│   ├── test_customer.py                # Customer list, form, detail, search, filter
│   ├── test_order.py                   # Order list, form, payment breakdown
│   ├── test_customer_hour.py           # Customer hour deduct, log, trainer report (เดิม: test_session.py)
│   ├── test_trainer.py                 # Trainer list, form, card view
│   ├── test_caretaker.py               # Caretaker list, form, branch filter
│   ├── test_package.py                 # Package list, form, status badge, scope
│   ├── test_booking.py                 # Timetable, slot click, color coding, confirm
│   ├── test_user.py                    # User list, form, slide-out panel
│   ├── test_permission.py              # Permission matrix, toggle, propagation (owner+)
│   ├── test_branch.py                  # Branch config, source types, opening hours
│   ├── test_signature_print.py         # Google Drive connect, generate, storage
│   ├── test_settings.py                # Language, dark mode, Google account, change password
│   ├── test_help.py                    # Help page, role-specific manual, LINE QR
│   ├── test_activity_log.py            # Activity log page, filters (branch_master+)
│   ├── test_cross_cutting.py           # UUID check, toast, loading state, responsive
│   ├── test_security_fe.py             # Token expiry, localStorage, XSS, route guard
│   ├── test_persistence.py             # Dark mode, language, filter state
│   └── test_error_handling.py          # Error boundary, network timeout, 401/403/404
│
└── integration/                        # End-to-end integration tests
    ├── conftest.py                     # Full-stack fixtures (real DB + browser)
    ├── test_auth_flow.py               # Complete login→temp token→PIN→JWT→dashboard
    ├── test_customer_lifecycle.py      # Create → view → edit → delete
    ├── test_order_session_flow.py      # Order → hour allocation → deduct
    ├── test_booking_flow.py            # Create → confirm → notify → cancel
    ├── test_role_access_flow.py        # Each role's scope and restrictions
    ├── test_permission_propagation.py  # Permission change → immediate effect
    ├── test_payment_flow.py            # Installment → outstanding → receipt
    ├── test_cancel_policy_flow.py      # Cancel → hour return / no return
    ├── test_branch_config_flow.py      # Create branch → customer code
    ├── test_data_consistency.py        # Cross-table balance consistency
    └── test_concurrent.py             # Race conditions (hour deduct, code generation)
```

---

## 2.5 BE — Allure Logging

### ทำไมต้องใช้ Allure
Allure คือ test reporting framework ที่แสดง report แบบ interactive ทำให้เห็นว่า test แต่ละตัวทำอะไร, ส่ง request อะไรไป, ได้ response อะไรกลับมา — ช่วยมากตอน debug ว่า test fail เพราะอะไร

### Install
```bash
pip install allure-pytest
# ติดตั้ง allure CLI สำหรับ generate report
brew install allure
```

### `tests/be/helpers/allure_helper.py`

```python
# tests/be/helpers/allure_helper.py
#
# Helper functions สำหรับ log ข้อมูลต่างๆ เข้า Allure report
# ใช้ใน BE tests เพื่อบันทึกทุก action ที่เกิดขึ้นระหว่าง test

import json
import allure
from httpx import Response


def log_request(method: str, url: str, payload: dict = None, headers: dict = None) -> None:
    """
    Log HTTP request ที่ส่งออกไปเข้า Allure report
    ทำให้เห็นชัดว่า test ส่ง request อะไร และ payload เป็นอะไร
    """
    # สร้าง step ชื่อ "REQUEST method url" ใน Allure
    with allure.step(f"REQUEST {method.upper()} {url}"):

        # ถ้ามี payload → แสดงเป็น JSON attachment ใน report
        if payload:
            allure.attach(
                body=json.dumps(payload, ensure_ascii=False, indent=2),
                name="Request Body",
                attachment_type=allure.attachment_type.JSON,
            )

        # ถ้ามี headers → แสดงใน report (ซ่อน Authorization value เพื่อ security)
        if headers:
            safe_headers = {
                k: "***" if k.lower() == "authorization" else v
                for k, v in headers.items()
            }
            allure.attach(
                body=json.dumps(safe_headers, indent=2),
                name="Request Headers",
                attachment_type=allure.attachment_type.JSON,
            )


def log_response(response: Response) -> None:
    """
    Log HTTP response ที่ได้รับกลับมาเข้า Allure report
    ทำให้เห็นชัดว่า API ตอบกลับด้วย status code อะไร และ body เป็นอะไร
    """
    # สร้าง step ชื่อ "RESPONSE status_code" ใน Allure
    with allure.step(f"RESPONSE {response.status_code}"):

        # พยายาม parse response body เป็น JSON ก่อน
        try:
            body = response.json()
            body_str = json.dumps(body, ensure_ascii=False, indent=2)
            attachment_type = allure.attachment_type.JSON
        except Exception:
            # ถ้า parse ไม่ได้ ให้แสดงเป็น text แทน
            body_str = response.text
            attachment_type = allure.attachment_type.TEXT

        allure.attach(
            body=body_str,
            name=f"Response Body ({response.status_code})",
            attachment_type=attachment_type,
        )


def log_step(description: str):
    """
    Decorator/context manager สำหรับ log business step ใน Allure
    ใช้เพื่อแบ่ง test เป็น steps ที่อ่านเข้าใจง่ายใน report

    ใช้แบบ context manager:
        with log_step("Create customer in Pattaya branch"):
            response = await client.post("/customers", ...)

    ใช้แบบ decorator:
        @log_step("Verify session balance decremented")
        async def check_balance():
            ...
    """
    return allure.step(description)


def log_db_check(description: str, result) -> None:
    """
    Log ผลการ query database โดยตรง ใช้เมื่อต้องการตรวจสอบ DB state
    เช่น ตรวจว่า password ถูก hash แล้ว หรือ balance ไม่ติดลบ
    """
    with allure.step(f"DB CHECK: {description}"):
        allure.attach(
            body=str(result),
            name="DB Result",
            attachment_type=allure.attachment_type.TEXT,
        )
```

### `tests/be/conftest.py` — เพิ่ม Allure fixtures

```python
# เพิ่มส่วน Allure ใน conftest.py

import allure
import pytest
from helpers.allure_helper import log_request, log_response


@pytest.fixture(autouse=True)
def allure_test_metadata(request):
    """
    autouse=True = ทำงานทุก test อัตโนมัติโดยไม่ต้องระบุ
    ใส่ metadata ให้ทุก test อัตโนมัติ เช่น ชื่อ test file, module, marker
    ทำให้ Allure report จัดกลุ่ม tests ได้ง่ายขึ้น
    """
    # ดึงชื่อ module จาก test file path เช่น test_auth_api → Auth API
    module_name = request.node.module.__name__.replace("test_", "").replace("_api", "").title()

    # ติด label ให้ test ใน Allure report
    allure.dynamic.feature(module_name)          # จัดกลุ่มตาม feature เช่น "Auth", "Customer"
    allure.dynamic.story(request.node.name)      # ชื่อ test function เป็น story
    allure.dynamic.severity(allure.severity_level.NORMAL)  # default severity


async def api_call(client, method: str, url: str, token: str = None,
                   json: dict = None, params: dict = None) -> Response:
    """
    Wrapper สำหรับ httpx call ที่ log ทุกอย่างเข้า Allure อัตโนมัติ
    ใช้แทนการ call client.get/post/put/delete โดยตรง เพื่อให้ทุก API call ถูก log

    ตัวอย่างใช้งาน:
        response = await api_call(client, "POST", "/customers",
                                  token=admin_token, json=payload)
    """
    # เตรียม headers พร้อม Authorization ถ้ามี token
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Log request เข้า Allure ก่อนส่ง
    log_request(method, url, payload=json, headers=headers)

    # ส่ง HTTP request จริง
    response = await getattr(client, method.lower())(
        url, json=json, params=params, headers=headers
    )

    # Log response เข้า Allure หลังได้รับ
    log_response(response)

    return response
```

### ตัวอย่าง Test ที่ใช้ Allure

```python
# tests/be/test_auth_api.py — ตัวอย่างการใช้ Allure ใน test จริง

import allure
import pytest
from helpers.allure_helper import log_step, log_db_check
from conftest import api_call


@allure.title("Login with valid credentials returns temporary token")
@allure.severity(allure.severity_level.BLOCKER)  # BLOCKER = ถ้า fail ทุกอย่างหยุด
@pytest.mark.be
async def test_login_valid_credentials(client, seed_data):
    """
    TC-API-AUTH-01
    ตรวจสอบว่า POST /auth/login ด้วย credentials ที่ถูกต้อง
    จะได้ temporary token กลับมา (ยังไม่ใช่ JWT จริง — JWT จะออกหลัง PIN เท่านั้น)
    """

    # Step 1: เตรียม payload
    with log_step("Prepare login payload"):
        payload = {
            "email": "owner@test.com",
            "password": "test_pass",
        }

    # Step 2: ส่ง request (log อัตโนมัติผ่าน api_call)
    with log_step("Send POST /auth/login"):
        response = await api_call(client, "POST", "/auth/login", json=payload)

    # Step 3: ตรวจสอบ response
    with log_step("Assert response"):
        # ต้องได้ 200 OK
        assert response.status_code == 200, (
            f"Expected 200 but got {response.status_code}. "
            "Login with valid credentials should always return 200."
        )

        data = response.json()

        # ต้องมี temporary_token (ไม่ใช่ JWT เต็ม — PIN ยังไม่ผ่าน)
        assert "temporary_token" in data, (
            "Response must contain 'temporary_token' after email+password login. "
            "JWT will only be issued after PIN verification."
        )

        # temporary_token ต้องไม่ว่าง
        assert data["temporary_token"], "temporary_token must not be empty"


@allure.title("PIN lockout after 5 wrong attempts")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.be
@pytest.mark.security
async def test_pin_lockout_after_five_attempts(client, seed_data, db_session):
    """
    TC-API-AUTH-12
    ตรวจสอบว่าหลังจากใส่ PIN ผิด 5 ครั้งติดต่อกัน
    account จะถูก lock และได้ 423 Locked กลับมา
    """

    with log_step("Login to get temporary token"):
        login_resp = await api_call(client, "POST", "/auth/login",
                                    json={"email": "admin@test.com", "password": "test_pass"})
        temp_token = login_resp.json()["temporary_token"]

    with log_step("Submit wrong PIN 5 times"):
        # ส่ง PIN ผิด 5 ครั้ง — ครั้งที่ 5 ควร lock account
        for attempt in range(1, 6):
            with log_step(f"Wrong PIN attempt {attempt}/5"):
                response = await api_call(
                    client, "POST", "/auth/pin/verify",
                    token=temp_token,
                    json={"pin": "000000"},  # PIN ผิดตั้งใจ
                )

    with log_step("Assert account is locked on 5th attempt"):
        # ครั้งที่ 5 ต้องได้ 423 Locked
        assert response.status_code == 423, (
            f"Expected 423 Locked after 5 wrong PINs but got {response.status_code}. "
            "Account must be locked to prevent brute force attacks."
        )
        assert "locked" in response.json()["detail"].lower()

    with log_step("Verify pin_locked flag in DB"):
        # ตรวจสอบ DB โดยตรงว่า pin_locked = True จริง
        user = db_session.query(User).filter_by(email="admin@test.com").first()
        log_db_check("user.pin_locked after 5 wrong attempts", user.pin_locked)
        assert user.pin_locked is True, "DB must have pin_locked=True after lockout"
```

### รัน Allure Report

```bash
# รัน tests พร้อม generate Allure results
pytest tests/be/ -v --alluredir=allure-results

# Generate และเปิด HTML report
allure serve allure-results

# หรือ generate เป็น static HTML folder
allure generate allure-results -o allure-report --clean
open allure-report/index.html
```

---

```python
# tests/be/conftest.py
#
# ไฟล์นี้ประกาศ fixtures ที่ใช้ร่วมกันทุก BE test
# pytest จะโหลดไฟล์นี้อัตโนมัติก่อนรัน test ใดๆ ใน folder be/

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.database import Base, get_db
from api.models import *     # import all models so Base knows all tables
from api.config import settings


# ─── Database Setup ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """
    สร้าง SQLAlchemy engine เชื่อมกับ test database
    scope="session" = สร้างครั้งเดียวต่อการรัน pytest ทั้งหมด (ประหยัด time)
    """
    # ใช้ database URL แยกสำหรับ test เพื่อไม่กระทบ development DB
    engine = create_engine(settings.TEST_DATABASE_URL)

    # สร้าง tables ทั้งหมดตาม models ที่ import ไว้
    Base.metadata.create_all(bind=engine)

    yield engine  # ส่ง engine ให้ test ใช้

    # หลัง session เสร็จสิ้น ลบ tables ทั้งหมดเพื่อ clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    สร้าง database session สำหรับแต่ละ test function
    scope="function" = สร้างและ rollback ทุกครั้งที่ test จบ
    ทำให้ tests แยกจากกัน ไม่มีข้อมูลตกค้างระหว่าง tests
    """
    # สร้าง connection และเริ่ม transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # สร้าง session จาก connection นั้น
    TestSession = sessionmaker(bind=connection)
    session = TestSession()

    yield session  # ส่ง session ให้ test ใช้

    # หลัง test จบ → rollback ทุกอย่างที่ทำในชั้น test นี้
    # ทำให้ DB กลับสู่สถานะเดิมก่อน test
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
async def client(db_session):
    """
    สร้าง httpx AsyncClient สำหรับยิง API requests ใน test
    override get_db dependency ให้ใช้ test session แทน production session
    """
    # แทนที่ get_db dependency ด้วย test session
    # ทำให้ API ใช้ DB เดียวกับที่ test กำลัง control อยู่
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # สร้าง async HTTP client ที่ยิงไปยัง FastAPI app โดยตรง (ไม่ต้องรัน server จริง)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # ล้าง dependency override หลัง test เสร็จ
    app.dependency_overrides.clear()


# ─── Seed Data ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def seed_data(test_engine):
    """
    สร้างข้อมูลพื้นฐานที่ทุก test ต้องการ
    - 1 partner
    - 3 branches (Pattaya, Chachoengsao, Kanchanaburi)
    - 1 user ต่อ role (developer, owner, branch_master, admin, trainer)
    scope="session" = สร้างครั้งเดียว ใช้ร่วมกันทั้งหมด
    """
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()

    # สร้าง partner หลัก
    partner = Partner(name="Test Partner", is_active=True)
    session.add(partner)
    session.flush()  # flush เพื่อให้ได้ partner.id ก่อน commit

    # สร้าง 3 สาขา
    branches = [
        Branch(partner_id=partner.id, name="Pattaya", prefix="BPY",
               opening_time="09:00", closing_time="21:00"),
        Branch(partner_id=partner.id, name="Chachoengsao", prefix="BCC",
               opening_time="09:00", closing_time="21:00"),
        Branch(partner_id=partner.id, name="Kanchanaburi", prefix="BKB",
               opening_time="09:00", closing_time="21:00"),
    ]
    session.add_all(branches)
    session.flush()

    # สร้าง source types สำหรับแต่ละ branch
    for branch in branches:
        session.add_all([
            SourceType(branch_id=branch.id, label="Page", code="MKT"),
            SourceType(branch_id=branch.id, label="Walk In", code="PAT"),
        ])

    # สร้าง users สำหรับแต่ละ role
    users = {
        "developer": User(partner_id=partner.id, username="developer",
                          email="developer@test.com",
                          password_hash=hash_password("test_pass"),
                          role="DEVELOPER"),
        "owner":     User(partner_id=partner.id, username="owner",
                          email="owner@test.com",
                          password_hash=hash_password("test_pass"),
                          role="OWNER"),
        # ... สร้าง branch_master, admin, trainer สำหรับแต่ละ branch
    }
    session.add_all(users.values())
    session.commit()

    yield {
        "partner": partner,
        "branches": branches,
        "users": users,
    }

    session.close()


# ─── Auth Token Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def auth_token(seed_data):
    """
    Factory fixture: รับ role แล้วคืน JWT token ที่ผ่าน PIN แล้ว
    ใช้: token = auth_token("admin")
    """
    def _get_token(role: str) -> str:
        # สร้าง JWT token จาก user ของ role นั้น
        # token นี้ผ่าน PIN แล้ว (pin_verified_at set แล้ว) พร้อมใช้งานทุก API
        user = seed_data["users"][role]
        return create_jwt_token(user_id=user.id, pin_verified=True)
    return _get_token


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


# ─── Factory Helpers ────────────────────────────────────────────────────────────

@pytest.fixture
def create_customer(db_session, seed_data):
    """
    Factory fixture: สร้าง test customer แล้วคืน id
    ใช้: customer_id = create_customer(branch="pattaya", source="MKT")
    """
    def _create(branch: str = "pattaya", source_code: str = "MKT",
                status: str = "ACTIVE", **kwargs) -> str:
        # หา branch และ source type จาก seed data
        branch_obj = next(b for b in seed_data["branches"]
                         if b.name.lower() == branch.lower())
        source_type = db_session.query(SourceType).filter_by(
            branch_id=branch_obj.id, code=source_code).first()

        # สร้าง customer code (ใช้ service function เดียวกับ production)
        code = generate_customer_code(
            branch_prefix=branch_obj.prefix,
            source_code=source_code,
            db=db_session
        )

        customer = Customer(
            partner_id=branch_obj.partner_id,
            branch_id=branch_obj.id,
            source_type_id=source_type.id,
            customer_code=code,
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "Customer"),
            status=status,
        )
        db_session.add(customer)
        db_session.flush()  # flush เพื่อได้ id โดยไม่ commit

        # สร้าง session balance เริ่มต้น = 0
        db_session.add(CustomerHourBalance(customer_id=customer.id, remaining=0))
        db_session.flush()

        return str(customer.id)
    return _create


@pytest.fixture
def create_trainer(db_session, seed_data):
    """Factory: สร้าง test trainer แล้วคืน id"""
    def _create(branch: str = "pattaya", status: str = "ACTIVE", **kwargs) -> str:
        branch_obj = next(b for b in seed_data["branches"]
                         if b.name.lower() == branch.lower())
        trainer = Trainer(
            branch_id=branch_obj.id,
            name=kwargs.get("name", "Test Trainer"),
            status=status,
        )
        db_session.add(trainer)
        db_session.flush()
        return str(trainer.id)
    return _create


@pytest.fixture
def create_package(db_session, seed_data):
    """Factory: สร้าง test package แล้วคืน id"""
    def _create(branch_scope: str = "ALL", hours: int = 10,
                price: float = 5000, **kwargs) -> str:
        package = Package(
            partner_id=seed_data["partner"].id,
            name=kwargs.get("name", "Test Package"),
            hours=hours,
            sale_type=kwargs.get("sale_type", "SALE"),
            price=price,
            branch_scope=branch_scope,
            is_active=True,
        )
        db_session.add(package)
        db_session.flush()
        return str(package.id)
    return _create


@pytest.fixture
def create_order(db_session, seed_data, create_customer, create_package):
    """Factory: สร้าง test order แล้วคืน id (พร้อม allocate hours)"""
    def _create(hours: int = 10, bonus_hours: int = 0, **kwargs) -> str:
        # สร้าง customer และ package ถ้าไม่ได้ระบุมา
        customer_id = kwargs.get("customer_id") or create_customer()
        package_id = kwargs.get("package_id") or create_package()
        branch_id = seed_data["branches"][0].id  # Pattaya default

        order = Order(
            partner_id=seed_data["partner"].id,
            branch_id=branch_id,
            customer_id=customer_id,
            package_id=package_id,
            order_date=date.today(),
            hours=hours,
            bonus_hours=bonus_hours,
            payment_method="BANK_TRANSFER",
            total_price=5000,
            paid_amount=5000,
        )
        db_session.add(order)
        db_session.flush()

        # อัปเดต customer hour balance หลังสร้าง order
        balance = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id).with_for_update().first()
        balance.remaining += hours + bonus_hours
        db_session.flush()

        return str(order.id)
    return _create
```

---

## 4. BE — Test Files & Functions

### `test_auth_api.py`

```python
# tests/be/test_auth_api.py
# ทดสอบ authentication endpoints ทั้งหมด
# TC-API-AUTH-01 ถึง TC-API-AUTH-15

# ─── POST /auth/login ───────────────────────────────────────────────────────────
async def test_login_valid_credentials(client)
    # TC-AUTH-01: ส่ง email+password ที่ถูกต้อง → ได้ temporary token กลับมา

async def test_login_wrong_password(client)
    # TC-AUTH-02: ส่ง password ผิด → 401 Unauthorized

async def test_login_unknown_email(client)
    # TC-AUTH-03: ส่ง email ที่ไม่มีในระบบ → 401 Unauthorized

async def test_login_empty_fields(client)
    # ส่ง payload ว่างเปล่า → 422 Unprocessable Entity

async def test_login_brute_force_protection(client)
    # TC-AUTH-14: ส่ง password ผิด 10 ครั้งติดต่อกัน → 429 Too Many Requests

# ─── POST /auth/pin/verify ──────────────────────────────────────────────────────
async def test_pin_verify_valid(client, seed_data)
    # TC-AUTH-04: ส่ง PIN ถูก → ได้ JWT จริงกลับมา (JWT ออกหลัง PIN เท่านั้น)

async def test_pin_verify_wrong(client, seed_data)
    # TC-AUTH-05: ส่ง PIN ผิด → 401 Unauthorized

async def test_pin_lockout_after_five_attempts(client, seed_data)
    # TC-AUTH-12: ส่ง PIN ผิด 5 ครั้ง → 423 Locked

async def test_pin_session_expiry(client, seed_data)
    # TC-AUTH-06 (BE): JWT ที่ PIN หมดอายุแล้ว (>5h) → 401 เมื่อ call protected API

# ─── POST /auth/pin/forgot ──────────────────────────────────────────────────────
async def test_pin_forgot_valid_email(client, seed_data)
    # TC-AUTH-06: ส่ง email → 200 OK, OTP ส่งไป mock email

async def test_pin_forgot_rate_limit(client, seed_data)
    # TC-AUTH-13: ขอ OTP 3 ครั้งใน 60 วิ → 429 Too Many Requests

# ─── POST /auth/pin/reset ───────────────────────────────────────────────────────
async def test_pin_reset_valid_otp(client, seed_data)
    # TC-AUTH-07: ส่ง OTP ถูก + new_pin → 200 OK, PIN เปลี่ยนแล้ว

async def test_pin_reset_expired_otp(client, seed_data)
    # TC-AUTH-08: ส่ง OTP หมดอายุ → 400 Bad Request

# ─── POST /auth/password/forgot ─────────────────────────────────────────────────
async def test_password_forgot_sends_email(client, seed_data)
    # ขอ reset password → 200 OK, email ส่งไป mock inbox

async def test_password_forgot_unknown_email(client)
    # ส่ง email ที่ไม่มี → 200 OK (ไม่บอกว่า email ไม่มี เพื่อ security)

# ─── POST /auth/password/reset ──────────────────────────────────────────────────
async def test_password_reset_valid_token(client, seed_data)
    # ส่ง token + new_password → 200 OK, password เปลี่ยนแล้ว, login ด้วย password ใหม่ได้

async def test_password_reset_expired_token(client, seed_data)
    # ส่ง token หมดอายุ → 400 Bad Request

# ─── POST /auth/password/change ─────────────────────────────────────────────────
async def test_password_change_success(client, owner_token)
    # ส่ง old_password + new_password → 200 OK

async def test_password_change_wrong_old_password(client, owner_token)
    # ส่ง old_password ผิด → 401 Unauthorized

# ─── POST /auth/logout ──────────────────────────────────────────────────────────
async def test_logout_invalidates_token(client, admin_token)
    # TC-AUTH-11: logout แล้วใช้ token เดิม → 401 Unauthorized

# ─── Protected Routes ───────────────────────────────────────────────────────────
async def test_protected_route_without_token(client)
    # TC-AUTH-09: เรียก /customers โดยไม่มี token → 401 Unauthorized

async def test_protected_route_with_expired_token(client)
    # TC-AUTH-10: เรียก /customers ด้วย JWT หมดอายุ → 401 Unauthorized

async def test_token_cross_partner_isolation(client, seed_data)
    # TC-AUTH-15: ใช้ token ของ Partner A เรียก branch ของ Partner B → 403 Forbidden

# ─── Internal API ───────────────────────────────────────────────────────────────
async def test_internal_assign_password(client)
    # Developer API key → assign password ใหม่ให้ user → 200 OK

async def test_internal_assign_pin(client)
    # Developer API key → assign PIN + unlock pin_locked → 200 OK

async def test_internal_requires_developer_key(client, admin_token)
    # ใช้ JWT ปกติ (ไม่ใช่ developer key) → 403 Forbidden
```

---

### `test_customer_api.py`

```python
# tests/be/test_customer_api.py
# TC-API-CUST-01 ถึง TC-API-CUST-19

# ─── GET /customers ─────────────────────────────────────────────────────────────
async def test_customer_list_paginated(client, admin_token, create_customer)
    # TC-CUST-01: ได้ list พร้อม pagination { items, total, page }
    # Assert: ไม่มี UUID ใน name/nickname/trainer_name fields

async def test_admin_sees_own_branch_only(client, admin_token, create_customer)
    # TC-CUST-02: admin Pattaya → เห็นแค่ลูกค้า Pattaya

async def test_trainer_sees_own_branch_only(client, trainer_token, create_customer)
    # TC-CUST-02b: trainer Pattaya → เห็นแค่ลูกค้า Pattaya

async def test_branch_master_sees_own_branch_only(client, branch_master_token, create_customer)
    # TC-CUST-02c: branch_master Pattaya → เห็นแค่ลูกค้า Pattaya

async def test_owner_sees_all_branches(client, owner_token, create_customer)
    # TC-CUST-03: owner → เห็นลูกค้าทุกสาขาใน partner

async def test_developer_sees_all_partners(client, developer_token, create_customer)
    # TC-CUST-03b: developer → เห็นลูกค้าทุก partner

async def test_customer_search_by_name(client, admin_token, create_customer)
    # TC-CUST-04: ?search=นาม → กรองได้ถูกต้อง

async def test_customer_filter_by_branch_and_status(client, owner_token, create_customer)
    # TC-CUST-05: ?branch=pattaya&status=active → กรองได้ถูกต้อง

async def test_customer_pagination_page2(client, owner_token, create_customer)
    # TC-CUST-15: ?page=2&page_size=10 → ได้ items ชุดที่ 2

async def test_customer_page_size_limit(client, admin_token)
    # TC-CUST-16: ?page_size=999 → 400 Bad Request

# ─── POST /customers ─────────────────────────────────────────────────────────────
async def test_create_customer_valid(client, admin_token, seed_data)
    # TC-CUST-06: สร้างลูกค้าครบ fields → 201 Created, code format BPY-MKT001

async def test_customer_code_auto_increment(client, admin_token, seed_data)
    # TC-CUST-07: สร้าง 2 ลูกค้า (branch+source เดิม) → code เพิ่มทีละ 1

async def test_create_customer_missing_required_field(client, admin_token, seed_data)
    # TC-CUST-08: ขาด first_name → 422 Unprocessable Entity

async def test_create_customer_trainer_wrong_branch(client, admin_token, seed_data)
    # TC-CUST-09: trainer จาก Kanchanaburi ใส่ใน Pattaya customer → 400 Bad Request

async def test_create_customer_invalid_email(client, admin_token, seed_data)
    # TC-CUST-17: email format ผิด → 422 Unprocessable Entity

async def test_create_customer_name_too_long(client, admin_token, seed_data)
    # TC-CUST-18: first_name ยาวเกิน 255 chars → 422 Unprocessable Entity

async def test_create_customer_concurrent_unique_code(client, admin_token, seed_data)
    # TC-CUST-19: สร้าง 2 customers พร้อมกัน (race condition) → codes unique ทั้งคู่

# ─── GET /customers/:id ──────────────────────────────────────────────────────────
async def test_get_customer_detail(client, admin_token, create_customer)
    # TC-CUST-10: ได้ detail ครบ + order_history + session_remaining

async def test_get_customer_not_found(client, admin_token)
    # TC-CUST-11: id ที่ไม่มี → 404 Not Found

# ─── PUT /customers/:id ──────────────────────────────────────────────────────────
async def test_update_customer(client, admin_token, create_customer)
    # TC-CUST-12: แก้ phone number → 200 OK, ข้อมูลอัปเดต

# ─── DELETE /customers/:id ───────────────────────────────────────────────────────
async def test_owner_can_delete_customer(client, owner_token, create_customer)
    # TC-CUST-13: owner ลบ → 204 No Content

async def test_branch_master_can_delete_customer(client, branch_master_token, create_customer)
    # TC-CUST-13b: branch_master ลบ → 204 No Content

async def test_trainer_cannot_delete_customer(client, trainer_token, create_customer)
    # TC-CUST-14: trainer ลบ → 403 Forbidden

async def test_admin_cannot_delete_when_matrix_disallows(client, admin_token, create_customer)
    # TC-CUST-14b: admin (customer.delete=false) → 403 Forbidden
```

---

### `test_order_api.py`

```python
# tests/be/test_order_api.py
# TC-API-ORDER-01 ถึง TC-API-ORDER-16

async def test_order_list_paginated(client, admin_token, create_order)
async def test_order_list_date_filter(client, admin_token, create_order)
async def test_order_list_has_outstanding_flag(client, admin_token, create_order)
async def test_create_order_valid(client, admin_token, create_customer, create_package)
    # Assert: hour_balance เพิ่มขึ้น hours + bonus_hours, activity log สร้าง

async def test_create_order_expired_package(client, admin_token, create_customer, create_package)
async def test_create_order_wrong_branch_package(client, admin_token, create_customer)
async def test_create_order_missing_fields(client, admin_token)
async def test_create_order_package_not_yet_active(client, admin_token, create_customer, create_package)
async def test_create_order_negative_hours(client, admin_token)
async def test_create_order_negative_price(client, admin_token)
async def test_get_order_detail_with_payment(client, admin_token, create_order)
async def test_update_order_notes(client, admin_token, create_order)
async def test_trainer_cannot_create_order(client, trainer_token)
async def test_admin_blocked_by_permission_matrix(client, admin_token)

# Payment
async def test_record_installment_payment(client, admin_token, create_order)
async def test_get_payment_history(client, admin_token, create_order)
async def test_send_receipt_email(client, admin_token, create_order)
```

---

### `test_customer_hour_api.py`

```python
# tests/be/test_customer_hour_api.py
# เปลี่ยนชื่อจาก session → customer_hour ทุกที่
# TC-API-SESS-01 ถึง TC-API-SESS-12

async def test_deduct_hour_valid(client, admin_token, create_order)
    # balance ลด 1, transaction log สร้าง type=HOUR_DEDUCT

async def test_deduct_hour_zero_balance(client, admin_token, create_customer)
    # balance=0 → 400 Bad Request

async def test_get_hour_log(client, admin_token, create_order)
    # ได้ list พร้อม fields ครบ ไม่มี UUID

async def test_hour_log_filter(client, admin_token, create_order)
async def test_trainer_report(client, admin_token, create_order)
async def test_get_remaining_hours(client, admin_token, create_order)
async def test_get_remaining_hours_not_found(client, admin_token)
async def test_trainer_sees_only_own_report(client, trainer_token)
async def test_manual_adjust_positive(client, admin_token, create_order)
async def test_manual_adjust_negative(client, admin_token, create_order)
async def test_manual_adjust_below_zero_blocked(client, admin_token, create_order)
async def test_concurrent_deduction_race_condition(client, admin_token, create_order)
    # 2 requests พร้อมกัน balance=1 → 1 สำเร็จ, 1 ล้มเหลว, final balance=0 (never -1)
```

---

### `test_booking_api.py`

```python
# tests/be/test_booking_api.py
# TC-API-BOOK-01 ถึง TC-API-BOOK-15

async def test_get_bookings_list(client, admin_token)
async def test_admin_create_booking(client, admin_token, create_customer, create_trainer)
async def test_trainer_schedules_own_slot(client, trainer_token, seed_data)
async def test_trainer_cannot_book_for_other(client, trainer_token, create_trainer)
async def test_confirm_booking(client, admin_token, create_customer, create_trainer)
    # Assert: status=CONFIRMED, LINE notify flag ถ้ามี LINE

async def test_trainer_cannot_confirm(client, trainer_token)
async def test_cancel_booking_admin(client, admin_token, create_customer, create_trainer)
async def test_trainer_cannot_cancel(client, trainer_token)
async def test_external_booking_valid(client)
async def test_external_booking_noncontiguous_slots(client)
async def test_external_booking_cross_day(client)
async def test_cancel_returns_hour_when_policy_true(client, admin_token, create_order)
async def test_cancel_no_return_when_policy_false(client, admin_token, create_order)
async def test_get_bookings_date_filter(client, admin_token)
async def test_get_bookings_trainer_filter(client, admin_token, create_trainer)

# Cancel Policy
async def test_get_cancel_policy(client, owner_token)
async def test_update_cancel_policy(client, owner_token)
async def test_admin_cannot_update_cancel_policy(client, admin_token)
```

---

### `test_permission_api.py`

```python
# tests/be/test_permission_api.py
# TC-API-PERM-01 ถึง TC-API-PERM-04

async def test_developer_sees_all_columns(client, developer_token)
async def test_owner_sees_subordinate_columns_only(client, owner_token)
    # Assert: ไม่มี 'developer' หรือ 'owner' key ใน response

async def test_branch_master_sees_admin_trainer_only(client, branch_master_token)
async def test_admin_has_no_permission_access(client, admin_token)
async def test_trainer_has_no_permission_access(client, trainer_token)
async def test_developer_can_update_any_role(client, developer_token)
async def test_owner_can_update_subordinate_roles(client, owner_token)
async def test_owner_cannot_update_developer(client, owner_token)
async def test_branch_master_can_update_admin_trainer(client, branch_master_token)
async def test_branch_master_cannot_update_owner(client, branch_master_token)
async def test_admin_cannot_update_permissions(client, admin_token)
async def test_trainer_cannot_update_permissions(client, trainer_token)
async def test_disabled_feature_returns_403(client, admin_token, owner_token)
    # owner ปิด booking → admin GET /bookings → 403 Feature not enabled
```

---

### `test_security.py`

```python
# tests/be/test_security.py
# TC-API-SEC-01 ถึง TC-API-SEC-03

async def test_sql_injection_query_param(client, admin_token)
    # ?search='; DROP TABLE customers; -- → 200 หรือ 400, ไม่มี DB error

async def test_sql_injection_body_field(client, admin_token, seed_data)
    # first_name = "'; DROP TABLE customers; --" → บันทึกเป็น plain text

async def test_token_cross_partner_isolation(client, seed_data)
    # owner token Partner A → GET /customers?branch_id=Partner B's branch → 403
```

---

### `test_data_integrity.py`

```python
# tests/be/test_data_integrity.py
# TC-API-INT-01 ถึง TC-API-INT-05

async def test_cannot_delete_branch_with_customers(client, owner_token, create_customer)
async def test_cannot_delete_trainer_with_booking(client, admin_token, create_trainer)
async def test_cannot_delete_package_with_orders(client, owner_token, create_order)
async def test_hour_balance_never_negative(client, admin_token, create_order, db_session)
    # 2 concurrent deductions, balance=1 → DB constraint, final=0 ไม่ใช่ -1

async def test_customer_code_unique_at_db_level(client, admin_token, seed_data, db_session)
```

---

## 5.5 FE — Locator Fallback System

### แนวคิด
- **Primary locator:** `page.get_by_test_id("testid")` → ใช้ `data-testid` attribute
- **Fallback locator:** `page.locator("//xpath")` → ใช้เมื่อ testid ไม่พบ
- **`STRICT_LOCATOR=true`** → ห้าม fallback, raise Exception ทันที (สำหรับ production test)
- **`STRICT_LOCATOR=false`** (default) → fallback ได้, บันทึกว่า test นั้นใช้ fallback

### ประโยชน์
ตอน FE ยังพัฒนาอยู่ อาจยังไม่มี `data-testid` ครบทุก element
Fallback ทำให้ test ยังรันได้โดยใช้ XPath แทน โดยบันทึกไว้ว่าต้องกลับมาเพิ่ม testid ทีหลัง

### `.env.test`

```env
# .env.test — Environment สำหรับ test
# โหลดด้วย: python-dotenv หรือ export ก่อนรัน pytest

# ─── Locator Mode ───────────────────────────────────────────────────────────────
# STRICT_LOCATOR=true  → ต้องมี data-testid เสมอ, fallback ไม่ได้, raise Exception
# STRICT_LOCATOR=false → fallback ไปใช้ XPath ได้ถ้าไม่มี data-testid
STRICT_LOCATOR=false

# ─── App URLs ───────────────────────────────────────────────────────────────────
FE_BASE_URL=http://localhost:5173
BE_BASE_URL=http://localhost:8000

# ─── Test Database ──────────────────────────────────────────────────────────────
TEST_DATABASE_URL=postgresql://studio_user:test_pass@localhost:5432/studio_test

# ─── Test Credentials ───────────────────────────────────────────────────────────
TEST_ADMIN_EMAIL=admin@test.com
TEST_ADMIN_PASSWORD=test_pass
TEST_ADMIN_PIN=123456
```

### `tests/fe/helpers/locator.py`

```python
# tests/fe/helpers/locator.py
#
# Fallback locator helpers สำหรับ Playwright tests
# ทุก interaction กับ UI element ควรผ่าน functions ในไฟล์นี้
# เพื่อให้ระบบ fallback ทำงานได้ครบทุก element

import os
import allure
from playwright.sync_api import Page, Locator

# อ่าน env ครั้งเดียวตอน import module
# ถ้า STRICT_LOCATOR=true → ไม่ fallback, raise Exception ทันที
# ถ้า STRICT_LOCATOR=false หรือไม่ได้ set → fallback ได้ (default)
STRICT_LOCATOR = os.getenv("STRICT_LOCATOR", "false").lower() == "true"


def _get_locator(page: Page, testid: str, xpath: str,
                 request=None) -> tuple[Locator, bool]:
    """
    Internal helper: คืน locator ที่ถูกต้องพร้อม flag ว่าใช้ fallback หรือเปล่า

    Logic:
    1. ลอง get_by_test_id(testid) ก่อน
    2. ถ้าพบ element → ใช้ได้เลย (fallback_used=False)
    3. ถ้าไม่พบ:
       - STRICT_LOCATOR=true → raise Exception
       - STRICT_LOCATOR=false → ใช้ XPath fallback (fallback_used=True)
    """
    # ลอง primary locator ก่อน (data-testid)
    primary = page.get_by_test_id(testid)

    # ตรวจสอบว่า element นั้นมีอยู่จริงใน DOM หรือเปล่า
    if primary.count() > 0:
        # พบ element ด้วย testid → ใช้ primary locator
        return primary, False

    # ไม่พบ element ด้วย testid
    if STRICT_LOCATOR:
        # Strict mode: ห้าม fallback → raise Exception ทันที
        # ใช้ตอน production testing เพื่อบังคับให้ใส่ data-testid ครบ
        raise Exception(
            f"[STRICT] Element not found: data-testid='{testid}'. "
            f"In strict mode, all elements must have data-testid attributes. "
            f"XPath fallback is disabled."
        )

    # Fallback mode: ใช้ XPath แทน
    # บันทึกว่า test นี้ใช้ fallback (เพื่อ report ภายหลัง)
    if request:
        # เก็บ testid ที่ไม่มีไว้ใน node เพื่อ report หลัง test เสร็จ
        if not hasattr(request.node, "fallback_used"):
            request.node.fallback_used = []
        request.node.fallback_used.append(testid)

    # Log ลง Allure ว่ากำลัง fallback
    allure.dynamic.parameter("fallback_xpath", xpath)

    return page.locator(xpath), True


def fill(page: Page, testid: str, xpath: str, value: str,
         request=None) -> None:
    """
    กรอกข้อมูลใน input field พร้อม fallback support
    ใช้แทน page.fill() หรือ locator.fill() โดยตรง

    ตัวอย่าง:
        fill(page, "email-input", "//input[@name='email']", "user@test.com", request)
    """
    with allure.step(f"Fill '{testid}' with value"):
        locator, used_fallback = _get_locator(page, testid, xpath, request)

        # ถ้าใช้ fallback → log เตือนใน Allure
        if used_fallback:
            allure.attach(
                body=f"testid='{testid}' not found. Used XPath fallback: {xpath}",
                name="⚠️ Fallback Used",
                attachment_type=allure.attachment_type.TEXT,
            )

        # กรอกข้อมูล
        locator.first.fill(value)


def click(page: Page, testid: str, xpath: str, request=None) -> None:
    """
    คลิก element พร้อม fallback support
    ใช้แทน page.click() หรือ locator.click() โดยตรง

    ตัวอย่าง:
        click(page, "login-submit", "//button[@type='submit']", request)
    """
    with allure.step(f"Click '{testid}'"):
        locator, used_fallback = _get_locator(page, testid, xpath, request)

        if used_fallback:
            allure.attach(
                body=f"testid='{testid}' not found. Used XPath fallback: {xpath}",
                name="⚠️ Fallback Used",
                attachment_type=allure.attachment_type.TEXT,
            )

        locator.first.click()


def select_option(page: Page, testid: str, xpath: str, value: str,
                  request=None) -> None:
    """
    เลือก option ใน dropdown พร้อม fallback support

    ตัวอย่าง:
        select_option(page, "branch-select", "//select[@name='branch']", "pattaya", request)
    """
    with allure.step(f"Select option '{value}' in '{testid}'"):
        locator, used_fallback = _get_locator(page, testid, xpath, request)

        if used_fallback:
            allure.attach(
                body=f"testid='{testid}' not found. Used XPath fallback: {xpath}",
                name="⚠️ Fallback Used",
                attachment_type=allure.attachment_type.TEXT,
            )

        locator.first.select_option(value)


def get_text(page: Page, testid: str, xpath: str, request=None) -> str:
    """
    อ่านข้อความจาก element พร้อม fallback support

    ตัวอย่าง:
        text = get_text(page, "customer-code", "//span[@class='customer-code']", request)
    """
    with allure.step(f"Get text from '{testid}'"):
        locator, used_fallback = _get_locator(page, testid, xpath, request)

        if used_fallback:
            allure.attach(
                body=f"testid='{testid}' not found. Used XPath fallback: {xpath}",
                name="⚠️ Fallback Used",
                attachment_type=allure.attachment_type.TEXT,
            )

        return locator.first.text_content()


def is_visible(page: Page, testid: str, xpath: str, request=None) -> bool:
    """
    ตรวจสอบว่า element มองเห็นอยู่หรือเปล่า พร้อม fallback support

    ตัวอย่าง:
        assert is_visible(page, "error-toast", "//div[@role='alert']", request)
    """
    with allure.step(f"Check visibility of '{testid}'"):
        locator, used_fallback = _get_locator(page, testid, xpath, request)

        if used_fallback:
            allure.attach(
                body=f"testid='{testid}' not found. Used XPath fallback: {xpath}",
                name="⚠️ Fallback Used",
                attachment_type=allure.attachment_type.TEXT,
            )

        return locator.first.is_visible()
```

### `tests/fe/helpers/fallback_report.py`

```python
# tests/fe/helpers/fallback_report.py
#
# สร้าง report สรุปว่า test ไหนบ้างที่ใช้ fallback XPath
# ใช้เพื่อ track ว่าต้องเพิ่ม data-testid ที่ไหนบ้าง

import allure
import pytest


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Hook ที่รันหลัง pytest เสร็จทั้งหมด
    แสดง summary ว่า test ไหนใช้ fallback บ้าง
    """
    # รวบรวม tests ที่มี fallback จาก test nodes ทั้งหมด
    fallback_tests = []

    for report in terminalreporter.stats.get("passed", []):
        node = report  # report object มี nodeid และ attribute ที่เราเพิ่มไว้
        if hasattr(node, "fallback_used") and node.fallback_used:
            fallback_tests.append({
                "test": node.nodeid,
                "missing_testids": node.fallback_used,
            })

    if fallback_tests:
        # แสดงใน terminal
        terminalreporter.write_sep("=", "FALLBACK LOCATOR REPORT")
        terminalreporter.write_line(
            f"⚠️  {len(fallback_tests)} test(s) used XPath fallback "
            f"(data-testid not found):"
        )
        for item in fallback_tests:
            terminalreporter.write_line(f"  • {item['test']}")
            for testid in item["missing_testids"]:
                terminalreporter.write_line(f"      → missing: data-testid='{testid}'")

        terminalreporter.write_line(
            "\n  💡 Add data-testid attributes to these elements "
            "to remove XPath dependency."
        )
```

### ตัวอย่าง Test ที่ใช้ Fallback Locator

```python
# tests/fe/test_auth.py — ตัวอย่างการใช้ fallback locator

import allure
import pytest
from helpers.locator import fill, click, is_visible

BASE_URL = "http://localhost:5173"


@allure.title("Login with valid credentials redirects to PIN page")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_login_valid_redirects_to_pin(page, request):
    """
    TC-AUTH-01
    ตรวจสอบว่า login ด้วย credentials ที่ถูกต้อง จะ redirect ไปหน้า /pin
    request parameter ใช้สำหรับ track fallback usage
    """

    with allure.step("Navigate to login page"):
        page.goto(f"{BASE_URL}/login")

    with allure.step("Fill email field"):
        # primary: data-testid="email-input"
        # fallback: XPath ถ้าไม่มี testid
        fill(page, "email-input", "//input[@name='email']",
             "admin@test.com", request)

    with allure.step("Fill password field"):
        fill(page, "password-input", "//input[@name='password']",
             "test_pass", request)

    with allure.step("Click submit button"):
        click(page, "login-submit", "//button[@type='submit']", request)

    with allure.step("Assert redirect to /pin"):
        # รอให้ redirect ไปหน้า PIN
        page.wait_for_url("**/pin", timeout=5000)

        # ตรวจว่า PIN input มองเห็นอยู่
        assert is_visible(page, "pin-input", "//input[@name='pin']", request), (
            "PIN input must be visible after successful email+password login. "
            "JWT is only issued after PIN verification."
        )
```

### pytest.ini — เพิ่ม Allure + env config

```ini
[pytest]

testpaths = tests

markers =
    be: Backend API tests
    fe: Frontend Playwright tests
    integration: End-to-end integration tests
    slow: Tests that take >5 seconds
    security: Security-related tests

addopts =
    -v
    --tb=short
    --strict-markers
    --alluredir=allure-results       # บันทึก Allure results ทุกครั้ง

asyncio_mode = auto

# โหลด env variables จาก .env.test อัตโนมัติ (ต้องติดตั้ง pytest-dotenv)
env_files = .env.test
```

---

```python
# tests/fe/conftest.py
# Playwright fixtures สำหรับ FE tests

import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# ─── Browser Setup ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser():
    """
    สร้าง browser instance ครั้งเดียวต่อการรัน test ทั้งหมด
    ใช้ Chromium เป็น default (สามารถเปลี่ยนเป็น Firefox/WebKit ได้)
    """
    with sync_playwright() as p:
        # launch=True แปลว่าเปิด browser จริงๆ (headless=False สำหรับ debug)
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """
    สร้าง browser context ใหม่สำหรับแต่ละ test
    context = เหมือน incognito window ใหม่ → ไม่มี cookie/state ตกค้าง
    """
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},  # Desktop viewport
        locale="th-TH",                            # ภาษาไทย
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """
    สร้าง page (tab) ใหม่สำหรับแต่ละ test
    """
    page = context.new_page()
    yield page
    page.close()


# ─── Login Helpers ──────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:5173"  # Vite dev server

# Test credentials ต้องตรงกับ seed data ใน BE
TEST_USERS = {
    "developer": {"email": "developer@test.com", "password": "test_pass", "pin": "123456"},
    "owner":     {"email": "owner@test.com",     "password": "test_pass", "pin": "123456"},
    "branch_master": {"email": "bm@test.com",   "password": "test_pass", "pin": "123456"},
    "admin":     {"email": "admin@test.com",     "password": "test_pass", "pin": "123456"},
    "trainer":   {"email": "trainer@test.com",   "password": "test_pass", "pin": "123456"},
}


def login_as(page: Page, role: str) -> None:
    """
    Helper: login เป็น role ที่กำหนด ผ่านทั้ง email+password และ PIN
    ใช้ใน test: login_as(page, role="admin")
    """
    user = TEST_USERS[role]

    # ไปหน้า login
    page.goto(f"{BASE_URL}/login")

    # กรอก email
    page.fill("[data-testid='email-input']", user["email"])

    # กรอก password
    page.fill("[data-testid='password-input']", user["password"])

    # กด submit
    page.click("[data-testid='login-submit']")

    # รอให้ redirect ไปหน้า PIN
    page.wait_for_url("**/pin")

    # กรอก PIN
    page.fill("[data-testid='pin-input']", user["pin"])

    # กด confirm
    page.click("[data-testid='pin-submit']")

    # รอให้ redirect ไปหน้า dashboard → login สำเร็จ
    page.wait_for_url("**/dashboard")


def assert_toast(page: Page, text: str, toast_type: str = "success") -> None:
    """
    Helper: ตรวจสอบว่า toast notification ปรากฏพร้อมข้อความที่กำหนด
    toast_type = "success" | "error"
    """
    # รอให้ toast ปรากฏ (timeout 5 วิ)
    toast = page.locator(f"[data-testid='toast-{toast_type}']")
    toast.wait_for(timeout=5000)

    # ตรวจสอบข้อความ
    assert text in toast.text_content(), (
        f"Expected toast to contain '{text}' but got '{toast.text_content()}'"
    )


def assert_table_row(page: Page, text: str) -> None:
    """
    Helper: ตรวจสอบว่ามี row ใน table ที่มีข้อความที่กำหนด
    """
    row = page.locator(f"[data-testid='table-row']:has-text('{text}')")
    assert row.count() > 0, f"Expected table to contain row with text '{text}'"


def assert_no_uuid_in_element(page: Page, selector: str) -> None:
    """
    Helper: ตรวจสอบว่าไม่มี UUID ใน element ที่กำหนด
    UUID format: 8-4-4-4-12 hex characters
    ใช้ป้องกัน bug จากระบบเก่าที่แสดง UUID แทนชื่อลูกค้า
    """
    import re
    uuid_pattern = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.IGNORECASE
    )
    elements = page.locator(selector).all_text_contents()
    for text in elements:
        assert not uuid_pattern.search(text), (
            f"Found raw UUID in UI element: '{text}'. "
            "Customers must be shown by name and code, never UUID."
        )
```

---

## 6. FE — Test Files & Functions

### `test_auth.py`

```python
# tests/fe/test_auth.py
# TC-AUTH-01 ถึง TC-AUTH-08 + Security

def test_login_valid_redirects_to_pin(page)
    # TC-AUTH-01: login สำเร็จ → redirect ไป /pin

def test_login_invalid_password_shows_error(page)
    # TC-AUTH-02: password ผิด → error message, ยังอยู่ /login

def test_login_empty_fields_validation(page)
    # TC-AUTH-03: กด submit ว่างๆ → validation error ทั้ง 2 fields

def test_pin_valid_redirects_to_dashboard(page)
    # TC-AUTH-04: PIN ถูก → redirect ไป /dashboard

def test_pin_wrong_shows_error(page)
    # TC-AUTH-05: PIN ผิด → error, input cleared, ยังอยู่ /pin

def test_pin_session_expiry_reprompts_pin(page)
    # TC-AUTH-06: simulate 5h expiry → redirect /pin ไม่ใช่ /login

def test_forgot_pin_otp_flow(page)
    # TC-AUTH-07: Forgot PIN → OTP → reset → login ด้วย PIN ใหม่ได้

def test_unauthenticated_redirects_to_login(page)
    # TC-AUTH-08: เข้า /customers โดยไม่ login → redirect /login
```

---

### `test_customer.py`

```python
# tests/fe/test_customer.py

def test_customer_list_loads(page)
def test_customer_search_realtime(page)
def test_customer_filter_by_branch(page)
def test_customer_filter_by_status(page)
def test_add_customer_happy_path(page)
    # Assert: toast success, customer ปรากฏใน list, code format BPY-XXXNNN

def test_trainer_chip_filters_by_branch(page)
    # เลือก Pattaya → trainer chips แสดงแค่ Pattaya trainers
    # เปลี่ยนเป็น Kanchanaburi → trainer chips เปลี่ยนทันที

def test_customer_form_required_validation(page)
def test_customer_code_format(page)
def test_customer_detail_shows_all_sections(page)
def test_edit_customer_prefills_form(page)
def test_delete_customer_confirms_first(page)
def test_customer_dropdown_shows_name_not_uuid(page)
    # Critical: ตรวจ dropdown ใน session deduct page ว่าไม่มี UUID
```

---

### `test_booking.py`

```python
# tests/fe/test_booking.py

def test_timetable_default_3day_view(page)
def test_toggle_to_full_week_view(page)
def test_slot_color_coding(page)
    # Staff=blue, Customer booking=teal, Pending=amber

def test_click_empty_slot_opens_popup(page)
def test_trainer_can_only_schedule_own_slots(page)
def test_admin_confirm_booking_line_prompt(page)
    # ลูกค้ามี LINE → prompt ปรากฏ

def test_admin_multi_select_slots(page)
def test_trainer_multi_select_own_slots(page)
def test_cancel_booking_removes_from_timetable(page)
def test_cancel_booking_returns_hour_policy_return(page)
def test_cancel_booking_no_return_policy(page)
def test_pending_external_booking_amber(page)
def test_confirm_external_pending(page)
def test_customer_no_line_no_notify_button(page)
def test_navigate_prev_next_3days(page)
```

---

### `test_cross_cutting.py`

```python
# tests/fe/test_cross_cutting.py

def test_all_tables_have_search(page)
    # ทดสอบ search box ใน: customers, orders, trainers, packages, users

def test_forms_show_loading_on_submit(page)
    # throttle network → กด submit → spinner ปรากฏ, ปุ่ม disabled

def test_success_toast_on_create(page)
def test_error_toast_on_server_error(page)
def test_no_uuid_anywhere_in_ui(page)
    # audit ทุก dropdown และ table cell ว่าไม่มี UUID

def test_confirmation_dialog_on_delete(page)
def test_tablet_responsive_768px(page)
    # viewport 768×1024 → sidebar adapts, tables scrollable

def test_thai_text_renders_without_clipping(page)
    # ใส่ข้อความภาษาไทย → ตรวจ line-height ว่า tone marks ไม่ถูก clip
```

---

### `test_error_handling.py`

```python
# tests/fe/test_error_handling.py

def test_js_error_boundary_shows_fallback(page)
    # mock component crash → fallback UI ปรากฏ ไม่ใช่ white screen

def test_network_timeout_shows_retry(page)
    # mock timeout → error state + "Retry" button

def test_401_redirects_to_login(page)
    # mock API 401 → redirect /login, session cleared

def test_403_shows_access_denied(page)
    # mock API 403 → "ไม่มีสิทธิ์เข้าถึง" page

def test_404_shows_not_found_page(page)
    # navigate ไป /nonexistent → custom 404 page
```

---

## 7. pytest.ini

```ini
# pytest.ini
# config file สำหรับ pytest — กำหนด paths, markers, และ options ต่างๆ

[pytest]

# บอก pytest ว่าให้หา test files ที่ไหน
testpaths = tests

# กำหนด markers สำหรับ filter tests
# ใช้: pytest -m be, pytest -m fe, pytest -m integration
markers =
    be: Backend API tests (pytest + httpx)
    fe: Frontend Playwright tests
    integration: End-to-end integration tests
    slow: Tests that take >5 seconds (skip with -m "not slow")
    security: Security-related tests

# options ที่ใช้ทุกครั้ง
addopts =
    -v                  # verbose: แสดงชื่อ test ทุกอัน
    --tb=short          # traceback แบบย่อ (อ่านง่ายกว่า long)
    --strict-markers    # error ถ้าใช้ marker ที่ไม่ได้ declare

# async mode สำหรับ BE tests (httpx AsyncClient)
asyncio_mode = auto
```

---

## 8. Quick Commands

```bash
# ─── Install ─────────────────────────────────────────────────────────────────────
pip install allure-pytest pytest-dotenv
brew install allure                     # Allure CLI สำหรับ generate report

# ─── BE Tests ────────────────────────────────────────────────────────────────────

# รัน BE tests + generate Allure results
pytest tests/be/ -v --alluredir=allure-results

# เปิด Allure report แบบ live server
allure serve allure-results

# รัน BE test file เดียว
pytest tests/be/test_auth_api.py -v --alluredir=allure-results

# ─── FE Tests ────────────────────────────────────────────────────────────────────

# รัน FE tests แบบ fallback mode (default, STRICT_LOCATOR=false)
pytest tests/fe/ -v --alluredir=allure-results

# รัน FE tests แบบ strict mode (ไม่ fallback, ต้องมี data-testid ครบ)
STRICT_LOCATOR=true pytest tests/fe/ -v --alluredir=allure-results

# รัน FE tests พร้อม headed browser (เห็น browser จริง — ใช้ตอน debug)
pytest tests/fe/ -v --headed --alluredir=allure-results

# ─── Integration Tests ────────────────────────────────────────────────────────────

pytest tests/integration/ -v --alluredir=allure-results

# ─── All Tests ───────────────────────────────────────────────────────────────────

pytest tests/ -v --alluredir=allure-results
allure serve allure-results

# ─── Parallel (เร็วขึ้น) ─────────────────────────────────────────────────────────

pip install pytest-xdist
pytest tests/be/ -n 4 -v --alluredir=allure-results

# ─── Filter ──────────────────────────────────────────────────────────────────────

pytest tests/ -m be -v                  # เฉพาะ BE
pytest tests/ -m fe -v                  # เฉพาะ FE
pytest tests/ -m security -v            # เฉพาะ security tests
pytest tests/ -m "not slow" -v          # ข้าม tests ที่นาน
```
