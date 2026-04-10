# tests/conftest.py  (วางที่ tests/ root)
#
# Root conftest — fixtures ที่ใช้ร่วมกันทั้ง BE, FE และ Integration layers
# pytest โหลดไฟล์นี้อัตโนมัติก่อนทุก test ใน tests/ folder
# เหตุผล: ป้องกันการ duplicate config และ fixtures ระหว่าง 3 layers

import os
import pytest

# โหลด .env.test ก่อนทุกอย่าง เพื่อให้ environment variables พร้อม
from dotenv import load_dotenv
load_dotenv(".env.test")


# ─── Shared Environment Fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url() -> str:
    """
    URL ของ BE API server สำหรับ integration tests
    อ่านจาก BE_BASE_URL ใน .env.test
    """
    # อ่าน URL จาก environment variable
    return os.getenv("BE_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def fe_base_url() -> str:
    """
    URL ของ FE Vite server สำหรับ Playwright tests
    อ่านจาก FE_BASE_URL ใน .env.test
    """
    return os.getenv("FE_BASE_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def developer_api_key() -> str:
    """
    Developer API key สำหรับ /internal/* endpoints
    อ่านจาก DEVELOPER_API_KEY ใน .env.test
    """
    return os.getenv("DEVELOPER_API_KEY", "test_dev_api_key_12345")


# ─── Shared Test Constants ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_credentials() -> dict:
    """
    Credentials สำหรับทุก role — ต้องตรงกับ seed data ใน BE conftest
    ใช้ใน FE (Playwright login) และ Integration tests
    """
    # อ่านจาก environment variables เพื่อ flexibility
    password = os.getenv("TEST_PASSWORD", "test_pass")
    pin = os.getenv("TEST_PIN", "123456")

    return {
        "developer":    {"email": "developer@test.com",  "password": password, "pin": pin},
        "owner":        {"email": "owner@test.com",       "password": password, "pin": pin},
        "branch_master":{"email": "bm_pattaya@test.com", "password": password, "pin": pin},
        "admin":        {"email": "admin@test.com",       "password": password, "pin": pin},
        "trainer":      {"email": "trainer@test.com",     "password": password, "pin": pin},
    }


# ─── Fallback Locator Report ─────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook ที่ทำงานหลังทุก test — ตรวจว่า test ไหนใช้ XPath fallback
    ถ้า test ใช้ fallback → เพิ่ม warning ใน report
    ใช้ติดตามว่า FE elements ไหนยังขาด data-testid
    """
    outcome = yield
    report = outcome.get_result()

    # ตรวจสอบว่า test node มี fallback_used attribute (set โดย common_web.py)
    if hasattr(item, "fallback_used") and item.fallback_used:
        # สร้าง warning สำหรับ testids ที่ไม่มีและต้อง fallback ไป XPath
        missing = ", ".join(item.fallback_used)
        report.sections.append((
            "⚠️ XPath Fallback Used",
            f"These testids were NOT found and fell back to XPath: {missing}\n"
            "Please add data-testid attributes to FE components."
        ))
