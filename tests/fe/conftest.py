# tests/fe/conftest.py  (วางที่ tests/fe/)
#
# FE-specific fixtures สำหรับ Playwright browser tests
# pytest โหลดไฟล์นี้อัตโนมัติก่อนทุก test ใน tests/fe/
# เหตุผล: แยก browser setup ออกจาก BE database setup เพื่อความชัดเจน

import os
import allure
import pytest
from playwright.sync_api import Page, Browser, BrowserContext, sync_playwright


# ─── Browser Configuration ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Override default browser context args ของ pytest-playwright
    เพิ่ม locale, timezone, viewport ให้ตรงกับ production environment ไทย
    """
    return {
        **browser_context_args,
        # ภาษาไทย สำหรับ date/number formatting
        "locale": "th-TH",

        # timezone ไทย
        "timezone_id": "Asia/Bangkok",

        # viewport ขนาด desktop (1440×900) — app เป็น desktop-first
        "viewport": {"width": 1440, "height": 900},

        # ignore HTTPS errors ใน test env (ใช้ HTTP localhost)
        "ignore_https_errors": True,
    }


# ─── Page Fixture ───────────────────────────────────────────────────────────────

@pytest.fixture
def page(context: BrowserContext):
    """
    สร้าง Page สำหรับแต่ละ test
    scope="function" (default) = แต่ละ test ได้ page ใหม่ที่สะอาด
    เหตุผล: ป้องกัน state ตกค้างระหว่าง tests (cookies, localStorage)
    """
    # สร้าง page ใหม่จาก context
    page = context.new_page()

    # หลัง test จบ → take screenshot ถ้า fail
    yield page

    # Teardown: ปิด page หลัง test
    page.close()


# ─── Screenshot on Failure ───────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook: เมื่อ test fail → take screenshot และ attach เข้า Allure
    ทำให้ debug ง่ายขึ้น เพราะเห็นว่า UI หน้าตาเป็นยังไงตอน fail
    """
    outcome = yield
    report = outcome.get_result()

    # ทำงานเฉพาะตอน test call phase (ไม่ใช่ setup/teardown) และ fail
    if report.when == "call" and report.failed:
        # ดึง page fixture จาก test
        page: Page = item.funcargs.get("page")
        if page:
            # Take screenshot ของ browser ตอน fail
            screenshot = page.screenshot(full_page=True)

            # Attach screenshot เข้า Allure report
            allure.attach(
                body=screenshot,
                name=f"Screenshot on Failure: {item.name}",
                attachment_type=allure.attachment_type.PNG,
            )


# ─── Allure Metadata ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def allure_fe_metadata(request):
    """
    autouse=True = ทำงานทุก FE test อัตโนมัติ
    ติด Allure labels ให้ทุก test สำหรับ report grouping
    """
    # ดึงชื่อ module จาก file path เช่น test_auth → Auth
    module_name = request.node.module.__name__.replace("test_", "").title()

    # ติด feature label
    allure.dynamic.feature(f"FE: {module_name}")

    # ติด story label (ชื่อ test function)
    allure.dynamic.story(request.node.name)

    # mark ว่าเป็น FE test
    allure.dynamic.tag("fe", "playwright")


