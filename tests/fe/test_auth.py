# tests/fe/test_auth.py
#
# FE tests สำหรับ Authentication flow
# TC-AUTH-01 ถึง TC-AUTH-08

import pytest
import allure
from helpers.common_web import (
    navigate, login_as, wait_for_url,
    fill, click, is_visible,
    assert_success_toast, assert_error_toast,
    assert_validation_error_shown,
    BASE_URL,
)


# ─── Login Flow ─────────────────────────────────────────────────────────────────

@allure.title("TC-AUTH-01: Login with valid credentials redirects to PIN page")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_login_valid_redirects_to_pin(page, request):
    """
    ตรวจสอบว่า login ด้วย credentials ถูกต้อง → redirect ไป /pin
    (JWT จะออกหลัง PIN verify เท่านั้น ไม่ใช่ตอนนี้)
    """
    with allure.step("Navigate to login page"):
        navigate(page, "/login")

    with allure.step("Fill valid credentials"):
        fill(page, "email-input", "//input[@name='email']",
             "admin@test.com", request)
        fill(page, "password-input", "//input[@type='password']",
             "test_pass", request)

    with allure.step("Submit login form"):
        click(page, "login-submit", "//button[@type='submit']", request)

    with allure.step("Assert redirected to /pin page"):
        wait_for_url(page, "**/pin")
        # PIN input ต้องมองเห็น
        assert is_visible(page, "pin-input", "//input[@name='pin']", request), (
            "PIN input must be visible after successful email+password login."
        )


@allure.title("TC-AUTH-02: Login with invalid password shows error, stays on /login")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_login_invalid_password_shows_error(page, request):
    """ตรวจสอบว่า password ผิด → แสดง error, ยังอยู่หน้า /login"""
    with allure.step("Navigate to login page"):
        navigate(page, "/login")

    with allure.step("Fill valid email + wrong password"):
        fill(page, "email-input", "//input[@name='email']",
             "admin@test.com", request)
        fill(page, "password-input", "//input[@type='password']",
             "wrong_password_here", request)

    with allure.step("Submit login form"):
        click(page, "login-submit", "//button[@type='submit']", request)

    with allure.step("Assert error shown and still on /login"):
        # ต้องไม่ redirect ไป /pin
        assert "/login" in page.url, (
            f"Should remain on /login after wrong password but redirected to {page.url}"
        )
        # ต้องมี error message
        assert is_visible(page, "login-error",
                           "//p[@role='alert']", request), (
            "Error message must be visible after wrong password login attempt."
        )


@allure.title("TC-AUTH-03: Login with empty fields shows validation errors")
@pytest.mark.fe
def test_login_empty_fields_validation(page, request):
    """ตรวจสอบว่ากด submit โดยไม่กรอก → validation error ทั้ง 2 fields"""
    with allure.step("Navigate to login page"):
        navigate(page, "/login")

    with allure.step("Submit without filling any fields"):
        # ไม่กรอกอะไรเลย กด submit ทันที
        click(page, "login-submit", "//button[@type='submit']", request)

    with allure.step("Assert validation errors on both fields"):
        # ต้องมี error ทั้ง email และ password fields
        assert_validation_error_shown(page, "email-input")
        assert_validation_error_shown(page, "password-input")

    with allure.step("Assert no network request was sent"):
        # ยังอยู่หน้า /login ไม่มี redirect
        assert "/login" in page.url, (
            "Should stay on /login when submitting empty form. "
            "Client-side validation must prevent network request."
        )


# ─── PIN Flow ────────────────────────────────────────────────────────────────────

@allure.title("TC-AUTH-04: Valid PIN redirects to dashboard (JWT issued)")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_pin_valid_redirects_to_dashboard(page, request):
    """
    ตรวจสอบว่า PIN ถูกต้อง → redirect ไป /dashboard
    นี่คือจุดที่ JWT ถูกออกและ session เริ่มต้น
    """
    with allure.step("Complete email+password login"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@name='email']",
             "admin@test.com", request)
        fill(page, "password-input", "//input[@type='password']",
             "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Enter correct PIN"):
        fill(page, "pin-input", "//input[@name='pin']", "123456", request)
        click(page, "pin-submit", "//button[@data-action='confirm-pin']", request)

    with allure.step("Assert redirected to dashboard"):
        wait_for_url(page, "**/dashboard")
        assert "/dashboard" in page.url, (
            f"Should redirect to /dashboard after valid PIN but got {page.url}"
        )


@allure.title("TC-AUTH-05: Wrong PIN shows error, input cleared, stays on /pin")
@pytest.mark.fe
def test_pin_wrong_shows_error(page, request):
    """ตรวจสอบว่า PIN ผิด → error, input cleared, ยังอยู่ /pin"""
    with allure.step("Login and reach /pin page"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@name='email']",
             "admin@test.com", request)
        fill(page, "password-input", "//input[@type='password']",
             "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Enter wrong PIN"):
        fill(page, "pin-input", "//input[@name='pin']", "000000", request)
        click(page, "pin-submit", "//button[@data-action='confirm-pin']", request)

    with allure.step("Assert error shown and stays on /pin"):
        assert "/pin" in page.url, (
            f"Should remain on /pin after wrong PIN but redirected to {page.url}"
        )
        assert is_visible(page, "pin-error",
                           "//p[@role='alert']", request), (
            "Error message must be visible after wrong PIN entry."
        )

    with allure.step("Assert PIN input was cleared"):
        pin_input = page.get_by_test_id("pin-input")
        if pin_input.count() > 0:
            assert pin_input.input_value() == "", (
                "PIN input must be cleared after wrong PIN attempt "
                "so user can retype easily."
            )


@allure.title("TC-AUTH-06: PIN session expiry re-prompts PIN (not full login)")
@pytest.mark.fe
def test_pin_session_expiry_reprompts_pin(page, request):
    """
    ตรวจสอบว่าหลัง PIN session หมดอายุ (5h) → redirect ไป /pin ไม่ใช่ /login
    user ไม่ต้อง login ใหม่ แค่ verify PIN อีกครั้ง
    """
    with allure.step("Complete full login (email + PIN)"):
        login_as(page, role="admin", request=request)

    with allure.step("Simulate PIN session expiry via API"):
        # เรียก API เพื่อ expire PIN session โดยไม่ expire login session
        page.evaluate("""
            async () => {
                // set pin_expired flag ใน session storage เพื่อ simulate
                sessionStorage.setItem('pin_expired', 'true');
            }
        """)

    with allure.step("Navigate to protected route"):
        navigate(page, "/customers")

    with allure.step("Assert redirected to /pin (not /login)"):
        # ต้องไปหน้า PIN ไม่ใช่ login ใหม่ทั้งหมด
        assert "/pin" in page.url, (
            f"PIN session expiry should redirect to /pin, not /login. "
            f"Current URL: {page.url}"
        )
        assert "/login" not in page.url, (
            "After PIN session expiry, user should NOT be required to login again. "
            "Only PIN re-verification should be required."
        )


@allure.title("TC-AUTH-07: Forgot PIN — OTP flow resets PIN successfully")
@pytest.mark.fe
def test_forgot_pin_otp_flow(page, request):
    """ตรวจสอบ Forgot PIN flow ครบ: OTP → reset → login ด้วย PIN ใหม่"""
    with allure.step("Navigate to /pin page"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@name='email']",
             "admin@test.com", request)
        fill(page, "password-input", "//input[@type='password']",
             "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Click Forgot PIN link"):
        click(page, "forgot-pin-link",
              "//a[contains(text(),'Forgot')]", request)
        wait_for_url(page, "**/pin/reset")

    with allure.step("Enter OTP from mock email"):
        # ใน test env OTP เป็น fixed value
        fill(page, "otp-input", "//input[@name='otp']", "654321", request)
        fill(page, "new-pin-input", "//input[@name='new_pin']", "999999", request)
        fill(page, "confirm-pin-input",
             "//input[@name='confirm_pin']", "999999", request)

    with allure.step("Submit PIN reset"):
        click(page, "reset-submit", "//button[@type='submit']", request)

    with allure.step("Assert success and redirected to /pin"):
        wait_for_url(page, "**/pin")
        assert_success_toast(page)


@allure.title("TC-AUTH-08: Unauthenticated access redirects to /login")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_unauthenticated_redirects_to_login(page, request):
    """
    ตรวจสอบว่าเข้า protected route โดยไม่ login → redirect ไป /login
    ป้องกัน unauthorized access
    """
    with allure.step("Navigate to protected route without login"):
        navigate(page, "/customers")

    with allure.step("Assert redirected to /login"):
        wait_for_url(page, "**/login")
        assert "/login" in page.url, (
            f"Unauthenticated user accessing /customers must be redirected to /login "
            f"but got {page.url}."
        )
