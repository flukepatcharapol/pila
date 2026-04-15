# tests/fe/test_auth.py
#
# FE Playwright tests สำหรับ Authentication flow (dual-session design)
#
# Auth architecture (design doc § 1):
#   Step 1: POST /auth/login  → opaque password_session_token (30 days), stored in localStorage
#   Step 2: POST /auth/pin/verify (Bearer: opaque) → access JWT (6 hours), stored in localStorage
#   Step 3: Access granted → Dashboard (requires access JWT via ProtectedRoute)
#
# Test groups:
#   TC-AUTH-*  : Core auth flow (login, PIN, error cases)
#   TC-FE-DS-* : Dual-session specific behavior (token shape, expiry, modal)

import json
import pytest
import allure
from helpers.common_web import (
    navigate, login_as, wait_for_url,
    fill, click, is_visible,
    assert_success_toast, assert_error_toast,
    assert_validation_error_shown,
    get_local_storage, expire_access_token, expire_password_session,
    is_jwt_shaped, assert_session_expired_modal_visible,
    click_session_expired_confirm, assert_tokens_cleared,
    mock_api_response, mock_api_error,
    BASE_URL,
)


# ─── Login Flow ─────────────────────────────────────────────────────────────────

@allure.title("TC-AUTH-01: Login with valid credentials redirects to PIN page")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_login_valid_redirects_to_pin(page, request):
    """
    ตรวจสอบว่า login ด้วย credentials ถูกต้อง → redirect ไป /pin
    JWT จะออกหลัง PIN verify เท่านั้น ไม่ใช่ตอนนี้ (design doc § 4)
    """
    with allure.step("Navigate to login page"):
        navigate(page, "/login")

    with allure.step("Fill valid credentials"):
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)

    with allure.step("Submit login form"):
        click(page, "login-submit", "//button[@type='submit']", request)

    with allure.step("Assert redirected to /pin page"):
        wait_for_url(page, "**/pin")
        assert is_visible(page, "pin-input", "//input[@id='pin']", request), (
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
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "wrong_password_here", request)

    with allure.step("Submit login form"):
        click(page, "login-submit", "//button[@type='submit']", request)

    with allure.step("Assert error shown and still on /login"):
        assert "/login" in page.url, (
            f"Should remain on /login after wrong password but redirected to {page.url}"
        )
        assert is_visible(page, "login-error", "//p[@data-testid='login-error']", request), (
            "Error message must be visible after wrong password login attempt."
        )


@allure.title("TC-AUTH-03: Login with empty fields shows error on submit")
@pytest.mark.fe
def test_login_empty_fields_stays_on_login(page, request):
    """
    ตรวจสอบว่ากด submit โดยไม่กรอก → HTML5 validation ป้องกัน form submit
    ยังคงอยู่ที่หน้า /login ไม่มี network request
    """
    with allure.step("Navigate to login page"):
        navigate(page, "/login")

    with allure.step("Submit without filling any fields"):
        click(page, "login-submit", "//button[@type='submit']", request)

    with allure.step("Assert still on /login (HTML5 validation blocks submit)"):
        assert "/login" in page.url, (
            "Should stay on /login when submitting empty form. "
            "HTML5 required attribute must prevent network request."
        )


# ─── PIN Flow ────────────────────────────────────────────────────────────────────

@allure.title("TC-AUTH-04: Valid PIN redirects to dashboard (access JWT issued)")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_pin_valid_redirects_to_dashboard(page, request):
    """
    ตรวจสอบว่า PIN ถูกต้อง → ได้ access JWT → redirect ไป /dashboard
    นี่คือจุดที่ access JWT ถูกออก (ไม่ใช่ตอน login) — design doc § 2.2
    """
    with allure.step("Complete email+password login"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Enter correct PIN"):
        fill(page, "pin-input", "//input[@id='pin']", "123456", request)
        click(page, "pin-submit", "//button[@data-testid='pin-submit']", request)

    with allure.step("Assert redirected to dashboard"):
        wait_for_url(page, "**/dashboard")
        assert "/dashboard" in page.url, (
            f"Should redirect to /dashboard after valid PIN but got {page.url}"
        )


@allure.title("TC-AUTH-05: Wrong PIN shows error, stays on /pin")
@pytest.mark.fe
def test_pin_wrong_shows_error(page, request):
    """ตรวจสอบว่า PIN ผิด → inline error, ยังอยู่ /pin, tokens ไม่ถูกลบ"""
    with allure.step("Login and reach /pin page"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Enter wrong PIN"):
        fill(page, "pin-input", "//input[@id='pin']", "000000", request)
        click(page, "pin-submit", "//button[@data-testid='pin-submit']", request)

    with allure.step("Assert inline error shown, stays on /pin"):
        assert "/pin" in page.url, (
            f"Should remain on /pin after wrong PIN but redirected to {page.url}"
        )
        assert is_visible(page, "pin-error", "//p[@data-testid='pin-error']", request), (
            "Inline error must be visible after wrong PIN. "
            "Design doc § 5.2.1: invalid_pin → inline error, stay at /pin."
        )

    with allure.step("Assert password_session_token NOT cleared (tokens intact)"):
        pwd_token = get_local_storage(page, "password_session_token")
        assert pwd_token is not None, (
            "password_session_token must NOT be cleared after wrong PIN attempt. "
            "Design doc § 8.3: invalid_pin → stay at /pin, do NOT clear tokens."
        )


@allure.title("TC-AUTH-06: Unauthenticated access to protected route redirects to /login")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_unauthenticated_redirects_to_login(page, request):
    """
    ตรวจสอบว่าเข้า protected route (/dashboard) โดยไม่มี token → redirect ไป /login
    ป้องกัน unauthorized access — ProtectedRoute guards the route
    """
    with allure.step("Navigate to /dashboard without any auth tokens"):
        # localStorage สะอาด (หน้าใหม่ต่อ test function)
        navigate(page, "/dashboard")

    with allure.step("Assert redirected to /login"):
        wait_for_url(page, "**/login")
        assert "/login" in page.url, (
            f"Unauthenticated user accessing /dashboard must be redirected to /login "
            f"but got {page.url}."
        )


# ─── Dual-Session Specific Tests (DS) ────────────────────────────────────────────
# Design doc: auth_dual_session_design.md § 10

@allure.title("TC-FE-DS-01: Login response stores opaque token (NOT JWT) in localStorage")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_login_stores_opaque_token_not_jwt(page, request):
    """
    Design doc § 3.1, § 14: login response คือ opaque string ไม่ใช่ JWT
    ตรวจสอบว่า:
    1. password_session_token ถูก store ใน localStorage
    2. ค่าที่ store ไม่มี 3 ส่วน (ไม่ใช่ JWT-shaped)
    3. password_session_expires_at ถูก store ด้วย
    """
    with allure.step("Login with valid credentials"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Assert opaque token stored in localStorage"):
        token = get_local_storage(page, "password_session_token")
        assert token is not None, (
            "password_session_token must be stored in localStorage after login. "
            "Design doc § 8.1: persist opaque password_session_token after login."
        )

    with allure.step("Assert token is NOT JWT-shaped (no 3-part dot structure)"):
        assert not is_jwt_shaped(token), (
            f"Login token must be opaque (not JWT). "
            f"Got token with {len(token.split('.'))} dot-separated parts. "
            "Design doc § 3.1 (Approach B): login returns opaque string, not JWT."
        )

    with allure.step("Assert password_session_expires_at stored"):
        expires_at = get_local_storage(page, "password_session_expires_at")
        assert expires_at is not None, (
            "password_session_expires_at must be stored in localStorage after login. "
            "Design doc § 8.1: store expires_at from login response expires_in."
        )
        assert int(expires_at) > 0, (
            "password_session_expires_at must be a positive timestamp (milliseconds since epoch)."
        )


@allure.title("TC-FE-DS-02: Successful PIN verify stores access JWT in localStorage")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.fe
def test_pin_verify_stores_access_jwt(page, request):
    """
    Design doc § 2.2, § 4: PIN verify คืน access JWT (6h) ไม่ใช่ opaque token
    ตรวจสอบว่า:
    1. access_token ถูก store ใน localStorage หลัง PIN verify สำเร็จ
    2. ค่าที่ store มี 3 ส่วน (JWT-shaped)
    3. ไม่มีการ store opaque token ใหม่ (password_session ยังเป็นของเดิม)
    """
    with allure.step("Complete full login (email + password)"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Get password_session_token before PIN (for comparison)"):
        token_before = get_local_storage(page, "password_session_token")

    with allure.step("Submit correct PIN"):
        fill(page, "pin-input", "//input[@id='pin']", "123456", request)
        click(page, "pin-submit", "//button[@data-testid='pin-submit']", request)
        wait_for_url(page, "**/dashboard")

    with allure.step("Assert access_token stored in localStorage"):
        access_token = get_local_storage(page, "access_token")
        assert access_token is not None, (
            "access_token must be stored in localStorage after successful PIN verify. "
            "Design doc § 8.1: store access_token (JWT) from pin/verify response."
        )

    with allure.step("Assert access_token IS JWT-shaped (header.payload.signature)"):
        assert is_jwt_shaped(access_token), (
            f"access_token must be JWT-shaped (3 dot-separated parts). "
            f"Got: {access_token[:50]}... "
            "Design doc § 4: access token is JWT with sub, role, pin_verified=true, exp."
        )

    with allure.step("Assert password_session_token unchanged (same opaque token)"):
        token_after = get_local_storage(page, "password_session_token")
        assert token_after == token_before, (
            "password_session_token must NOT change after PIN verify. "
            "Design doc: PIN verify issues a new access JWT, not a new password session."
        )


@allure.title("TC-FE-DS-03: Access JWT expires while password session valid → redirect /pin")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_access_jwt_expired_redirects_to_pin(page, request):
    """
    Design doc § 8.3 (scenario 2): หลัง access JWT หมดอายุ (6h) แต่ password session ยังใช้ได้
    → redirect ไป /pin (user ไม่ต้อง login ใหม่ด้วย email+password)

    ทดสอบโดย: login + PIN → ลบ access_token → navigate to /dashboard
    → ProtectedRoute เห็น token หายไป → password session ยังใช้ได้ → /pin
    """
    with allure.step("Complete full auth (email + PIN) to get both tokens"):
        login_as(page, role="admin", request=request)
        assert "/dashboard" in page.url, "Setup: should be on dashboard after full login"

    with allure.step("Simulate access JWT expiry (remove from localStorage)"):
        expire_access_token(page)
        access_token_gone = get_local_storage(page, "access_token")
        assert access_token_gone is None, "Setup: access_token must be removed"

    with allure.step("Navigate to protected route (/dashboard)"):
        navigate(page, "/dashboard")

    with allure.step("Assert redirected to /pin (NOT /login)"):
        # ProtectedRoute: no access_token + valid password_session → /pin
        wait_for_url(page, "**/pin", timeout=5000)
        assert "/pin" in page.url, (
            f"When access JWT expires but password session is valid, "
            f"user must be redirected to /pin to re-enter PIN only. "
            f"Got: {page.url}. "
            "Design doc § 8.3: re-enter PIN without full re-login."
        )
        assert "/login" not in page.url, (
            "User should NOT be redirected to /login when only the access JWT expired. "
            "Full re-login is only needed when the password session also expires."
        )

    with allure.step("Assert password_session_token still present"):
        pwd_token = get_local_storage(page, "password_session_token")
        assert pwd_token is not None, (
            "password_session_token must still exist after access JWT expiry. "
            "The opaque token is valid for 30 days — only the 6h access JWT expired."
        )


@allure.title("TC-FE-DS-04: Password session expired at PIN submit → session expired modal → /login")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_password_session_expired_shows_modal(page, request):
    """
    Design doc § 8.3 (scenario 3), § 5.2.1: password session หมดอายุ (30d)
    → POST /auth/pin/verify คืน 401 error_code=session_expired
    → แสดง modal "Session ของท่านหมดอายุแล้ว" (ไม่ใช่ inline error)
    → คลิก OK → clearAllTokens + redirect /login

    ทดสอบโดย: mock /auth/pin/verify ให้ return 401 session_expired
    """
    with allure.step("Login (email+password) to store password_session in localStorage"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Mock /auth/pin/verify to return 401 session_expired"):
        # Simulate server-side session expiry — server returns session_expired error_code
        mock_api_response(
            page,
            "**/auth/pin/verify",
            body={"error_code": "session_expired", "detail": "Session expired. Please log in again."},
            status=401,
        )

    with allure.step("Submit PIN (will hit mocked 401 session_expired)"):
        fill(page, "pin-input", "//input[@id='pin']", "123456", request)
        click(page, "pin-submit", "//button[@data-testid='pin-submit']", request)

    with allure.step("Assert session expired modal is visible with Thai message"):
        assert_session_expired_modal_visible(page)

    with allure.step("Click OK on modal to acknowledge"):
        click_session_expired_confirm(page)

    with allure.step("Assert redirected to /login"):
        wait_for_url(page, "**/login", timeout=5000)
        assert "/login" in page.url, (
            f"After session expired modal OK, user must be redirected to /login. "
            f"Got: {page.url}"
        )

    with allure.step("Assert all tokens cleared from localStorage"):
        assert_tokens_cleared(page)


@allure.title("TC-FE-DS-05: Session revoked at PIN submit → modal → /login (same as expired)")
@pytest.mark.fe
def test_session_revoked_shows_modal(page, request):
    """
    Design doc § 5.2.1: session_revoked (e.g. after logout from another device)
    → sama UI behavior as session_expired → modal → /login
    """
    with allure.step("Login to reach /pin"):
        navigate(page, "/login")
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)
        click(page, "login-submit", "//button[@type='submit']", request)
        wait_for_url(page, "**/pin")

    with allure.step("Mock /auth/pin/verify to return 401 session_revoked"):
        mock_api_response(
            page,
            "**/auth/pin/verify",
            body={"error_code": "session_revoked", "detail": "Session revoked. Please log in again."},
            status=401,
        )

    with allure.step("Submit PIN"):
        fill(page, "pin-input", "//input[@id='pin']", "123456", request)
        click(page, "pin-submit", "//button[@data-testid='pin-submit']", request)

    with allure.step("Assert session expired modal shown (same modal for revoked)"):
        assert_session_expired_modal_visible(page)

    with allure.step("Click OK and assert redirect to /login"):
        click_session_expired_confirm(page)
        wait_for_url(page, "**/login", timeout=5000)
        assert_tokens_cleared(page)


@allure.title("TC-FE-DS-06: Logout clears all tokens and redirects to /login")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_logout_clears_tokens_and_redirects(page, request):
    """
    Design doc § 5.5: POST /auth/logout → FE ต้อง clearAllTokens + redirect /login
    ตรวจสอบว่า:
    1. คลิก logout → access_token ถูกลบ
    2. password_session_token ถูกลบ
    3. redirect ไป /login
    """
    with allure.step("Complete full login to get both tokens"):
        login_as(page, role="admin", request=request)
        assert "/dashboard" in page.url, "Setup: must be on dashboard"

    with allure.step("Assert both tokens present before logout"):
        assert get_local_storage(page, "access_token") is not None, "Setup: access_token must exist"
        assert get_local_storage(page, "password_session_token") is not None, \
            "Setup: password_session_token must exist"

    with allure.step("Click logout button"):
        click(page, "logout-btn", "//button[@data-action='logout']", request)

    with allure.step("Assert redirected to /login"):
        wait_for_url(page, "**/login", timeout=5000)
        assert "/login" in page.url, (
            f"After logout, user must be redirected to /login. Got: {page.url}"
        )

    with allure.step("Assert all auth tokens cleared from localStorage"):
        assert_tokens_cleared(page)


@allure.title("TC-FE-DS-07: Re-enter PIN after JWT expiry restores access")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_re_pin_after_jwt_expiry_restores_access(page, request):
    """
    Design doc § 8.5 (sequence diagram 2): full happy path ของ 6h cycle
    1. Login + PIN → dashboard (มี access JWT)
    2. Simulate JWT expiry (ลบ access_token)
    3. Navigate to protected route → redirect /pin
    4. Enter PIN again → ได้ access JWT ใหม่ → dashboard (ใช้งานได้)
    """
    with allure.step("Step 1: Full login to dashboard"):
        login_as(page, role="admin", request=request)
        access_token_first = get_local_storage(page, "access_token")
        assert access_token_first is not None, "Setup: access_token must exist after login"

    with allure.step("Step 2: Simulate access JWT expiry"):
        expire_access_token(page)

    with allure.step("Step 3: Navigate to /dashboard → expect redirect to /pin"):
        navigate(page, "/dashboard")
        wait_for_url(page, "**/pin", timeout=5000)
        assert "/pin" in page.url, "Must redirect to /pin when access JWT expired"

    with allure.step("Step 4: Re-enter PIN → get new access JWT"):
        fill(page, "pin-input", "//input[@id='pin']", "123456", request)
        click(page, "pin-submit", "//button[@data-testid='pin-submit']", request)
        wait_for_url(page, "**/dashboard", timeout=5000)

    with allure.step("Assert back on dashboard with new access token"):
        assert "/dashboard" in page.url, (
            "After re-entering PIN, user must reach /dashboard again. "
            "Design doc § 8.5: password session allows PIN re-entry without full login."
        )
        access_token_new = get_local_storage(page, "access_token")
        assert access_token_new is not None, (
            "New access_token must be stored after second PIN verify."
        )
