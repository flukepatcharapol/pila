# tests/fe/helpers/common_web.py
#
# Shared helper functions สำหรับ FE Playwright tests ทั้งหมด
# ทุก test file ควร import จากที่นี่
# เหตุผล: ลด redundancy, รองรับ fallback locator, log เข้า Allure อัตโนมัติ

import os
import re
import allure
from playwright.sync_api import Page, expect

# ─── Config ─────────────────────────────────────────────────────────────────────

BASE_URL = os.getenv("FE_BASE_URL", "http://localhost:5173")

# STRICT_LOCATOR=true  → ต้องมี data-testid เสมอ ห้าม fallback
# STRICT_LOCATOR=false → fallback ไปใช้ XPath ได้ถ้าไม่มี data-testid
STRICT_LOCATOR = os.getenv("STRICT_LOCATOR", "false").lower() == "true"

# Test credentials ต้องตรงกับ seed data ใน BE
TEST_USERS = {
    "developer":    {"email": "developer@test.com",  "password": "test_pass", "pin": "123456"},
    "owner":        {"email": "owner@test.com",       "password": "test_pass", "pin": "123456"},
    "branch_master":{"email": "bm_pattaya@test.com", "password": "test_pass", "pin": "123456"},
    "admin":        {"email": "admin@test.com",       "password": "test_pass", "pin": "123456"},
    "trainer":      {"email": "trainer@test.com",     "password": "test_pass", "pin": "123456"},
}

# UUID pattern สำหรับตรวจสอบว่า UI ไม่ return UUID ดิบๆ
UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE
)


# ─── Navigation ─────────────────────────────────────────────────────────────────

def navigate(page: Page, path: str) -> None:
    """
    Navigate ไปยัง path ที่กำหนด พร้อม log เข้า Allure
    ใช้แทน page.goto() โดยตรงเพื่อให้ทุก navigation ถูก log

    ตัวอย่าง:
        navigate(page, "/customers")
    """
    url = f"{BASE_URL}{path}"
    with allure.step(f"Navigate to {path}"):
        page.goto(url)
        # รอให้ network idle ก่อนดำเนินการต่อ
        page.wait_for_load_state("networkidle")


def wait_for_url(page: Page, url_pattern: str, timeout: int = 5000) -> None:
    """
    รอให้ URL เปลี่ยนไปตาม pattern ที่กำหนด
    ใช้หลัง action ที่ทำให้เกิด redirect

    ตัวอย่าง:
        wait_for_url(page, "**/dashboard")
    """
    with allure.step(f"Wait for URL: {url_pattern}"):
        page.wait_for_url(url_pattern, timeout=timeout)


# ─── Auth Flow ──────────────────────────────────────────────────────────────────

def login_as(page: Page, role: str, request=None) -> None:
    """
    Login เป็น role ที่กำหนด ผ่านทั้ง email+password และ PIN
    ใช้ใน test setup หรือ fixture เพื่อไม่ต้อง repeat login steps

    ตัวอย่าง:
        login_as(page, role="admin", request=request)
    """
    user = TEST_USERS[role]

    with allure.step(f"Login as {role}"):
        # Step 1: ไปหน้า login
        navigate(page, "/login")

        # Step 2: กรอก email + password
        fill(page, "email-input", "//input[@name='email']", user["email"], request)
        fill(page, "password-input", "//input[@type='password']", user["password"], request)

        # Step 3: กด Submit
        click(page, "login-submit", "//button[@type='submit']", request)

        # Step 4: รอ redirect ไปหน้า PIN
        wait_for_url(page, "**/pin")

        # Step 5: กรอก PIN
        fill(page, "pin-input", "//input[@name='pin']", user["pin"], request)

        # Step 6: กด Confirm PIN
        click(page, "pin-submit", "//button[@data-action='confirm-pin']", request)

        # Step 7: รอ redirect ไปหน้า Dashboard (login สำเร็จ)
        wait_for_url(page, "**/dashboard")


def logout(page: Page, request=None) -> None:
    """Logout ออกจากระบบ"""
    with allure.step("Logout"):
        click(page, "logout-btn", "//button[@data-action='logout']", request)
        wait_for_url(page, "**/login")


# ─── Locator + Fallback ─────────────────────────────────────────────────────────

def _get_locator(page: Page, testid: str, xpath: str, request=None):
    """
    Internal: หา locator ที่ถูกต้องพร้อม fallback
    1. ลอง data-testid ก่อน
    2. ถ้าไม่พบ + STRICT_LOCATOR=true → raise Exception
    3. ถ้าไม่พบ + STRICT_LOCATOR=false → ใช้ XPath fallback
    """
    primary = page.get_by_test_id(testid)

    if primary.count() > 0:
        # พบ element ด้วย data-testid → ใช้ primary
        return primary, False

    if STRICT_LOCATOR:
        raise Exception(
            f"[STRICT] data-testid='{testid}' not found. "
            "In strict mode, all elements must have data-testid attributes."
        )

    # Fallback: บันทึก testid ที่ขาดหายไปเพื่อ report ภายหลัง
    if request and hasattr(request, "node"):
        if not hasattr(request.node, "fallback_used"):
            request.node.fallback_used = []
        request.node.fallback_used.append(testid)

    # Log fallback เข้า Allure
    allure.attach(
        body=f"data-testid='{testid}' not found → using XPath: {xpath}",
        name="⚠️ Fallback to XPath",
        attachment_type=allure.attachment_type.TEXT,
    )

    return page.locator(xpath), True


def fill(page: Page, testid: str, xpath: str, value: str, request=None) -> None:
    """
    กรอกข้อมูลใน input field พร้อม fallback support

    ตัวอย่าง:
        fill(page, "first-name-input", "//input[@name='first_name']", "John", request)
    """
    with allure.step(f"Fill '{testid}' = '{value}'"):
        locator, _ = _get_locator(page, testid, xpath, request)
        locator.first.fill(value)


def click(page: Page, testid: str, xpath: str, request=None) -> None:
    """
    คลิก element พร้อม fallback support

    ตัวอย่าง:
        click(page, "save-btn", "//button[@type='submit']", request)
    """
    with allure.step(f"Click '{testid}'"):
        locator, _ = _get_locator(page, testid, xpath, request)
        locator.first.click()


def select_option(page: Page, testid: str, xpath: str,
                  value: str, request=None) -> None:
    """
    เลือก option ใน dropdown/select พร้อม fallback support

    ตัวอย่าง:
        select_option(page, "branch-select", "//select[@name='branch']", "pattaya", request)
    """
    with allure.step(f"Select '{value}' in '{testid}'"):
        locator, _ = _get_locator(page, testid, xpath, request)
        locator.first.select_option(value)


def click_chip(page: Page, chip_text: str, request=None) -> None:
    """
    คลิก chip selector ตาม text ที่แสดง
    ใช้สำหรับ branch selector, trainer selector, source type selector ฯลฯ

    ตัวอย่าง:
        click_chip(page, "Pattaya", request)
        click_chip(page, "Teen:Pattaya", request)
    """
    with allure.step(f"Click chip: '{chip_text}'"):
        # หา chip โดย text content
        chip = page.locator(f"[data-testid='chip']:has-text('{chip_text}')")

        if chip.count() == 0:
            # fallback: หาด้วย role=button
            chip = page.locator(f"button:has-text('{chip_text}')")

        chip.first.click()


def get_text(page: Page, testid: str, xpath: str, request=None) -> str:
    """
    อ่าน text content จาก element พร้อม fallback support

    ตัวอย่าง:
        code = get_text(page, "customer-code", "//span[@class='customer-code']", request)
    """
    with allure.step(f"Get text from '{testid}'"):
        locator, _ = _get_locator(page, testid, xpath, request)
        return locator.first.text_content() or ""


def is_visible(page: Page, testid: str, xpath: str, request=None) -> bool:
    """
    ตรวจสอบว่า element มองเห็นอยู่หรือเปล่า พร้อม fallback support

    ตัวอย่าง:
        assert is_visible(page, "error-message", "//p[@role='alert']", request)
    """
    with allure.step(f"Check visibility: '{testid}'"):
        locator, _ = _get_locator(page, testid, xpath, request)
        return locator.first.is_visible()


def is_hidden(page: Page, testid: str, xpath: str, request=None) -> bool:
    """ตรวจสอบว่า element ถูกซ่อนอยู่"""
    with allure.step(f"Check hidden: '{testid}'"):
        locator, _ = _get_locator(page, testid, xpath, request)
        return locator.first.is_hidden()


# ─── Table Helpers ──────────────────────────────────────────────────────────────

def search_table(page: Page, query: str, request=None) -> None:
    """
    พิมพ์ข้อความค้นหาใน search bar ของ table แล้วรอให้ table update

    ตัวอย่าง:
        search_table(page, "ปัญฑกมล", request)
    """
    with allure.step(f"Search table: '{query}'"):
        fill(page, "table-search", "//input[@placeholder*='ค้นหา']", query, request)
        # รอให้ table reload หลังพิมพ์ (debounce)
        page.wait_for_timeout(500)


def get_table_row_count(page: Page) -> int:
    """นับจำนวน rows ใน data table"""
    with allure.step("Count table rows"):
        rows = page.locator("[data-testid='table-row']")
        return rows.count()


def assert_table_contains(page: Page, text: str) -> None:
    """ตรวจสอบว่า table มี row ที่มี text ที่กำหนด"""
    with allure.step(f"Assert table contains: '{text}'"):
        row = page.locator(f"[data-testid='table-row']:has-text('{text}')")
        assert row.count() > 0, (
            f"Table should contain a row with text '{text}' but none found."
        )


def assert_table_not_contains(page: Page, text: str) -> None:
    """ตรวจสอบว่า table ไม่มี row ที่มี text ที่กำหนด"""
    with allure.step(f"Assert table NOT contains: '{text}'"):
        row = page.locator(f"[data-testid='table-row']:has-text('{text}')")
        assert row.count() == 0, (
            f"Table should NOT contain a row with text '{text}' but found {row.count()}."
        )


def assert_no_uuid_in_table(page: Page) -> None:
    """
    ตรวจสอบว่าไม่มี UUID ดิบๆ ใน table cells ทั้งหมด
    ป้องกัน regression จากระบบเก่าที่แสดง UUID แทนชื่อจริง
    """
    with allure.step("Assert no raw UUIDs in table"):
        cells = page.locator("[data-testid='table-cell']").all_text_contents()
        for text in cells:
            assert not UUID_PATTERN.search(text), (
                f"Found raw UUID in table cell: '{text}'. "
                "Table must show human-readable values, not UUIDs."
            )


# ─── Form Helpers ────────────────────────────────────────────────────────────────

def click_add_button(page: Page, request=None) -> None:
    """คลิกปุ่ม Add/New ที่มักอยู่ด้านบนขวาของ list page"""
    with allure.step("Click Add button"):
        click(page, "add-btn", "//button[contains(@class,'btn-primary')]", request)


def click_save(page: Page, request=None) -> None:
    """คลิกปุ่ม Save ใน form"""
    with allure.step("Click Save"):
        click(page, "save-btn", "//button[@type='submit']", request)


def click_cancel(page: Page, request=None) -> None:
    """คลิกปุ่ม Cancel ใน form"""
    with allure.step("Click Cancel"):
        click(page, "cancel-btn", "//button[contains(text(),'Cancel')]", request)


def click_edit(page: Page, request=None) -> None:
    """คลิกปุ่ม Edit ใน detail page"""
    with allure.step("Click Edit"):
        click(page, "edit-btn", "//button[@data-action='edit']", request)


def click_delete(page: Page, request=None) -> None:
    """คลิกปุ่ม Delete แล้วยืนยัน confirm dialog"""
    with allure.step("Click Delete and confirm"):
        click(page, "delete-btn", "//button[@data-action='delete']", request)
        # ยืนยัน confirm dialog
        confirm_dialog(page, request)


def confirm_dialog(page: Page, request=None) -> None:
    """คลิก Confirm ใน confirmation dialog"""
    with allure.step("Confirm dialog"):
        click(page, "confirm-btn", "//button[@data-action='confirm']", request)


def click_table_row(page: Page, row_text: str) -> None:
    """คลิก row ใน table ที่มี text ที่กำหนด เพื่อเปิด detail"""
    with allure.step(f"Click table row: '{row_text}'"):
        row = page.locator(f"[data-testid='table-row']:has-text('{row_text}')")
        row.first.click()


# ─── Toast Assertions ────────────────────────────────────────────────────────────

def assert_success_toast(page: Page, text: str = None, timeout: int = 5000) -> None:
    """
    ตรวจสอบว่า success toast ปรากฏขึ้น
    ใช้หลัง save/create/update สำเร็จ

    ตัวอย่าง:
        assert_success_toast(page, "บันทึกสำเร็จ")
    """
    with allure.step(f"Assert success toast: '{text or 'any'}'"):
        toast = page.locator("[data-testid='toast-success']")
        toast.wait_for(timeout=timeout)

        if text:
            assert text in (toast.text_content() or ""), (
                f"Expected success toast to contain '{text}' "
                f"but got '{toast.text_content()}'"
            )


def assert_error_toast(page: Page, text: str = None, timeout: int = 5000) -> None:
    """ตรวจสอบว่า error toast ปรากฏขึ้น"""
    with allure.step(f"Assert error toast: '{text or 'any'}'"):
        toast = page.locator("[data-testid='toast-error']")
        toast.wait_for(timeout=timeout)

        if text:
            assert text in (toast.text_content() or ""), (
                f"Expected error toast to contain '{text}' "
                f"but got '{toast.text_content()}'"
            )


def assert_validation_error_shown(page: Page, field_testid: str) -> None:
    """ตรวจสอบว่า validation error แสดงใต้ field ที่กำหนด"""
    with allure.step(f"Assert validation error on field: '{field_testid}'"):
        error = page.locator(f"[data-testid='{field_testid}-error']")
        assert error.is_visible(), (
            f"Expected validation error to be visible for field '{field_testid}' "
            "but it is not shown."
        )


# ─── Loading State ────────────────────────────────────────────────────────────────

def assert_loading_skeleton_visible(page: Page) -> None:
    """ตรวจสอบว่า loading skeleton/shimmer แสดงอยู่"""
    with allure.step("Assert loading skeleton visible"):
        skeleton = page.locator("[data-testid='loading-skeleton']")
        assert skeleton.is_visible(), (
            "Loading skeleton should be visible while data is loading. "
            "This ensures good UX during slow network conditions."
        )


def assert_submit_button_loading(page: Page, request=None) -> None:
    """ตรวจสอบว่า submit button แสดง loading state และ disabled"""
    with allure.step("Assert submit button in loading state"):
        btn = _get_locator(page, "save-btn", "//button[@type='submit']", request)[0]
        assert btn.first.is_disabled(), (
            "Submit button must be disabled while submitting "
            "to prevent double submission."
        )


# ─── Dual-Session Storage Helpers ────────────────────────────────────────────────

def get_local_storage(page: Page, key: str) -> str | None:
    """
    อ่านค่าจาก localStorage ด้วย key ที่กำหนด
    คืน None ถ้าไม่มี key นั้น

    ตัวอย่าง:
        token = get_local_storage(page, 'access_token')
    """
    result = page.evaluate(f"() => localStorage.getItem('{key}')")
    return result  # type: ignore[return-value]


def expire_access_token(page: Page) -> None:
    """
    ลบ access_token ออกจาก localStorage เพื่อ simulate การหมดอายุของ JWT (6h)
    ทำให้ ProtectedRoute redirect ไป /pin (ถ้า password session ยังใช้ได้)

    Design doc § 8.3: "On 401 from protected API call... IF password_session_expires_at > now() → /pin"
    """
    with allure.step("Expire access token (remove from localStorage)"):
        page.evaluate("() => localStorage.removeItem('access_token')")


def expire_password_session(page: Page) -> None:
    """
    ตั้ง password_session_expires_at เป็นอดีต เพื่อ simulate การหมดอายุของ password session (30d)
    ทำให้ isPasswordSessionValid() คืน false

    Design doc § 8.3: เมื่อ password session หมด → modal → /login
    """
    with allure.step("Expire password session (set expires_at to past)"):
        page.evaluate("""
            () => {
                // ตั้ง expires_at เป็น 1ms (อดีต) เพื่อ simulate session expiry
                // password_session_token ยังอยู่ใน localStorage (opaque token)
                // แต่ isPasswordSessionValid() จะคืน false
                localStorage.setItem('password_session_expires_at', '1');
            }
        """)


def is_jwt_shaped(value: str) -> bool:
    """
    ตรวจสอบว่าค่าเป็น JWT format (header.payload.signature = 3 ส่วนคั่นด้วย .)
    ใช้ verify ว่า login response คืน opaque token (ไม่ใช่ JWT)

    Design doc § 3.1: opaque token ต้องไม่ใช่ JWT — ไม่มี 3 ส่วน
    """
    parts = value.split(".")
    return len(parts) == 3 and all(len(part) > 4 for part in parts)


def assert_session_expired_modal_visible(page: Page, timeout: int = 5000) -> None:
    """
    ตรวจสอบว่า SessionExpiredModal แสดงอยู่พร้อม Thai text ที่ถูกต้อง

    Design doc § 8.3: modal ต้องแสดง "Session ของท่านหมดอายุแล้ว\\nกรุณาเข้าสู่ระบบใหม่"
    """
    with allure.step("Assert session expired modal is visible with Thai text"):
        modal = page.locator("[data-testid='session-expired-modal']")
        modal.wait_for(state="visible", timeout=timeout)

        content = modal.text_content() or ""
        assert "Session ของท่านหมดอายุแล้ว" in content, (
            f"Session expired modal must contain 'Session ของท่านหมดอายุแล้ว' "
            f"per design doc § 8.3 but got: '{content}'"
        )


def click_session_expired_confirm(page: Page) -> None:
    """คลิกปุ่ม OK ใน SessionExpiredModal → trigger clearAllTokens + redirect /login"""
    with allure.step("Click OK on session expired modal"):
        page.locator("[data-testid='session-expired-confirm']").click()


def assert_tokens_cleared(page: Page) -> None:
    """
    ตรวจสอบว่า auth tokens ทั้งหมดถูกลบออกจาก localStorage แล้ว
    ใช้หลัง logout หรือ session expiry ที่ถูกต้อง

    Design doc § 8.4: ต้อง clear ทุก key หลัง session expired/logout
    """
    with allure.step("Assert all auth tokens cleared from localStorage"):
        pwd_token = get_local_storage(page, "password_session_token")
        access_token = get_local_storage(page, "access_token")
        assert pwd_token is None, (
            "password_session_token must be removed from localStorage after logout/expiry "
            "but it is still present. This is a security concern — token must be cleared."
        )
        assert access_token is None, (
            "access_token must be removed from localStorage after logout/expiry "
            "but it is still present. This is a security concern — token must be cleared."
        )


# ─── Network Helpers ──────────────────────────────────────────────────────────────

def set_slow_network(page: Page) -> None:
    """
    จำลอง slow 3G network สำหรับทดสอบ loading states
    ใช้ก่อน navigate เพื่อทดสอบ skeleton/loading behavior
    """
    with allure.step("Set slow 3G network"):
        page.context.set_offline(False)
        # ใช้ route interception เพื่อ delay responses
        page.route("**/api/**", lambda route: (
            page.wait_for_timeout(2000),
            route.continue_()
        ))


def mock_api_error(page: Page, url_pattern: str, status: int = 500) -> None:
    """
    Mock API error สำหรับทดสอบ error handling
    ใช้ทดสอบว่า UI จัดการ error ได้ถูกต้อง

    ตัวอย่าง:
        mock_api_error(page, "**/customers", status=500)
    """
    with allure.step(f"Mock API error {status} for: {url_pattern}"):
        page.route(url_pattern, lambda route: route.fulfill(
            status=status,
            body='{"detail": "Internal Server Error"}',
            headers={"Content-Type": "application/json"},
        ))


def mock_api_response(page: Page, url_pattern: str,
                      body: dict, status: int = 200) -> None:
    """
    Mock API response สำหรับทดสอบ UI behavior

    ตัวอย่าง:
        mock_api_response(page, "**/settings/google/storage",
                          body={"used_bytes": 5000000000, "total_bytes": 15000000000})
    """
    with allure.step(f"Mock API response for: {url_pattern}"):
        import json as json_lib
        page.route(url_pattern, lambda route: route.fulfill(
            status=status,
            body=json_lib.dumps(body),
            headers={"Content-Type": "application/json"},
        ))


# ─── Sidebar/Navigation Assertions ───────────────────────────────────────────────

def assert_sidebar_item_visible(page: Page, item_text: str) -> None:
    """ตรวจสอบว่า sidebar menu item มองเห็นอยู่"""
    with allure.step(f"Assert sidebar item visible: '{item_text}'"):
        item = page.locator(f"[data-testid='sidebar-item']:has-text('{item_text}')")
        assert item.is_visible(), (
            f"Sidebar item '{item_text}' should be visible for this role "
            "but it is hidden or not rendered."
        )


def assert_sidebar_item_hidden(page: Page, item_text: str) -> None:
    """ตรวจสอบว่า sidebar menu item ถูกซ่อนอยู่"""
    with allure.step(f"Assert sidebar item hidden: '{item_text}'"):
        item = page.locator(f"[data-testid='sidebar-item']:has-text('{item_text}')")
        assert not item.is_visible(), (
            f"Sidebar item '{item_text}' should be hidden for this role "
            "but it is visible — permission is not applied correctly."
        )


def assert_feature_disabled_overlay(page: Page) -> None:
    """ตรวจสอบว่า feature disabled overlay แสดงอยู่"""
    with allure.step("Assert feature disabled overlay"):
        overlay = page.locator("[data-testid='feature-disabled-overlay']")
        assert overlay.is_visible(), (
            "Feature disabled overlay should be visible when feature toggle is OFF. "
            "The overlay must show 'ฟีเจอร์นี้ไม่พร้อมใช้งาน'."
        )
        assert "ฟีเจอร์นี้ไม่พร้อมใช้งาน" in (overlay.text_content() or ""), (
            "Feature disabled overlay must contain Thai text 'ฟีเจอร์นี้ไม่พร้อมใช้งาน'."
        )
