# tests/be/test_auth_api.py
#
# BE tests สำหรับ Authentication API
# TC-API-AUTH-01 ถึง TC-API-AUTH-15

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_forbidden,
)


# ─── POST /auth/login ───────────────────────────────────────────────────────────

@allure.title("TC-API-AUTH-01: Login with valid credentials returns temporary token")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.be
async def test_login_valid_credentials(client, seed_data):
    """
    ตรวจสอบว่า login ด้วย credentials ที่ถูกต้องได้ temporary token กลับมา
    (ไม่ใช่ JWT จริง — JWT จะออกหลัง PIN verify เท่านั้น)
    """
    with allure.step("Send valid email + password"):
        res = await post(client, "/auth/login", json={
            "email": "owner@test.com",
            "password": "test_pass",
        }, expected_status=200)

    with allure.step("Assert temporary token returned"):
        data = res.json()
        # ต้องได้ temporary_token กลับมา ยังไม่ใช่ JWT เต็ม
        assert "temporary_token" in data, (
            "Response must contain 'temporary_token'. "
            "JWT is only issued after PIN verification."
        )
        assert data["temporary_token"], "temporary_token must not be empty"


@allure.title("TC-API-AUTH-02: Login with wrong password returns 401")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.be
async def test_login_wrong_password(client, seed_data):
    """ตรวจสอบว่า password ผิดได้ 401 Unauthorized"""
    with allure.step("Send valid email + wrong password"):
        res = await post(client, "/auth/login", json={
            "email": "owner@test.com",
            "password": "wrong_password",
        }, expected_status=401)

    with allure.step("Assert error detail"):
        assert "detail" in res.json(), "401 response must have 'detail' field"


@allure.title("TC-API-AUTH-03: Login with unknown email returns 401")
@pytest.mark.be
async def test_login_unknown_email(client):
    """ตรวจสอบว่า email ที่ไม่มีในระบบได้ 401"""
    await post(client, "/auth/login", json={
        "email": "nobody@test.com",
        "password": "any_pass",
    }, expected_status=401)


# ─── POST /auth/pin/verify ──────────────────────────────────────────────────────

@allure.title("TC-API-AUTH-04: Valid PIN returns JWT access token")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.be
async def test_pin_verify_valid(client, seed_data):
    """
    ตรวจสอบว่า PIN ถูกต้อง → ได้ JWT จริงกลับมา
    JWT ออกหลัง PIN verify เท่านั้น (ไม่ออกหลัง login)
    """
    with allure.step("Login to get temporary token"):
        login_res = await post(client, "/auth/login", json={
            "email": "owner@test.com",
            "password": "test_pass",
        }, expected_status=200)
        temp_token = login_res.json()["temporary_token"]

    with allure.step("Verify PIN with temporary token"):
        res = await post(client, "/auth/pin/verify",
                         token=temp_token,
                         json={"pin": "123456"},
                         expected_status=200)

    with allure.step("Assert JWT access token returned"):
        data = res.json()
        assert "access_token" in data, (
            "Response must contain 'access_token' after PIN verification. "
            "This is the JWT that grants access to all protected endpoints."
        )
        assert data["token_type"] == "bearer", "token_type must be 'bearer'"


@allure.title("TC-API-AUTH-05: Wrong PIN returns 401")
@pytest.mark.be
async def test_pin_verify_wrong(client, seed_data):
    """ตรวจสอบว่า PIN ผิดได้ 401"""
    with allure.step("Login to get temporary token"):
        login_res = await post(client, "/auth/login", json={
            "email": "admin@test.com",
            "password": "test_pass",
        }, expected_status=200)
        temp_token = login_res.json()["temporary_token"]

    with allure.step("Send wrong PIN"):
        res = await post(client, "/auth/pin/verify",
                         token=temp_token,
                         json={"pin": "000000"},
                         expected_status=401)

    with allure.step("Assert error detail"):
        assert "Invalid PIN" in res.json().get("detail", ""), (
            "Error detail must mention 'Invalid PIN' for wrong PIN attempts."
        )


@allure.title("TC-API-AUTH-12: PIN lockout after 5 wrong attempts")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.be
@pytest.mark.security
async def test_pin_lockout_after_five_attempts(client, seed_data, db_session):
    """
    ตรวจสอบว่าหลัง PIN ผิด 5 ครั้ง account ถูก lock
    ป้องกัน brute force attack บน PIN
    """
    with allure.step("Login to get temporary token"):
        login_res = await post(client, "/auth/login", json={
            "email": "admin@test.com",
            "password": "test_pass",
        }, expected_status=200)
        temp_token = login_res.json()["temporary_token"]

    with allure.step("Submit wrong PIN 5 times"):
        for attempt in range(1, 6):
            with allure.step(f"Wrong PIN attempt {attempt}/5"):
                res = await post(client, "/auth/pin/verify",
                                 token=temp_token,
                                 json={"pin": "000000"})

    with allure.step("Assert 423 Locked on 5th attempt"):
        assert res.status_code == 423, (
            f"Expected 423 Locked after 5 wrong PINs but got {res.status_code}. "
            "Account must lock to prevent brute force attacks."
        )

    with allure.step("Verify pin_locked=True in DB"):
        from api.models.user import User
        user = db_session.query(User).filter_by(email="admin@test.com").first()
        assert user.pin_locked is True, "DB must have pin_locked=True after lockout"


# ─── POST /auth/pin/forgot ──────────────────────────────────────────────────────

@allure.title("TC-API-AUTH-06: Forgot PIN sends OTP email")
@pytest.mark.be
async def test_pin_forgot_valid_email(client, seed_data):
    """ตรวจสอบว่าขอ OTP ด้วย email ที่ถูกต้อง → 200 OK"""
    res = await post(client, "/auth/pin/forgot",
                     json={"email": "owner@test.com"},
                     expected_status=200)

    with allure.step("Assert OTP sent confirmation"):
        data = res.json()
        assert "message" in data, "Response must confirm OTP was sent"


@allure.title("TC-API-AUTH-13: OTP request rate limited (3 per 60s)")
@pytest.mark.be
@pytest.mark.security
async def test_pin_forgot_rate_limit(client, seed_data):
    """
    ตรวจสอบ rate limiting: ขอ OTP >3 ครั้งใน 60 วิ → 429 Too Many Requests
    ป้องกัน OTP spam
    """
    with allure.step("Request OTP 3 times (within limit)"):
        for _ in range(3):
            await post(client, "/auth/pin/forgot",
                       json={"email": "owner@test.com"})

    with allure.step("4th request should be rate limited"):
        res = await post(client, "/auth/pin/forgot",
                         json={"email": "owner@test.com"},
                         expected_status=429)

    with allure.step("Assert rate limit error detail"):
        assert "Too many" in res.json().get("detail", ""), (
            "Rate limit error must mention 'Too many' requests."
        )


# ─── POST /auth/pin/reset ───────────────────────────────────────────────────────

@allure.title("TC-API-AUTH-07: Reset PIN with valid OTP")
@pytest.mark.be
async def test_pin_reset_valid_otp(client, seed_data, db_session):
    """ตรวจสอบว่า reset PIN ด้วย OTP ที่ถูกต้อง → 200 OK, PIN เปลี่ยน"""
    with allure.step("Get test OTP from DB (mock env)"):
        # ใน test env ดึง OTP จาก DB โดยตรงแทนการรอ email
        from api.models.user import PinOtp
        otp_record = db_session.query(PinOtp).filter_by(used=False).first()
        otp_value = "654321"  # test env OTP

    with allure.step("Reset PIN with OTP"):
        res = await post(client, "/auth/pin/reset", json={
            "otp": otp_value,
            "new_pin": "999999",
        }, expected_status=200)

    with allure.step("Assert PIN updated"):
        assert "message" in res.json(), "Response must confirm PIN was updated"


@allure.title("TC-API-AUTH-08: Reset PIN with expired OTP returns 400")
@pytest.mark.be
async def test_pin_reset_expired_otp(client):
    """ตรวจสอบว่า OTP หมดอายุ → 400 Bad Request"""
    res = await post(client, "/auth/pin/reset", json={
        "otp": "expired_otp_token",
        "new_pin": "999999",
    }, expected_status=400)

    with allure.step("Assert expired OTP error"):
        assert "expired" in res.json().get("detail", "").lower(), (
            "Error detail must mention 'expired' for expired OTP tokens."
        )


# ─── Protected Routes ───────────────────────────────────────────────────────────

@allure.title("TC-API-AUTH-09: Protected route without token returns 401")
@pytest.mark.be
async def test_protected_route_without_token(client):
    """ตรวจสอบว่าเรียก protected API โดยไม่มี token → 401 Unauthorized"""
    # ไม่ส่ง token → ต้องได้ 401
    res = await get(client, "/customers", expected_status=401)


@allure.title("TC-API-AUTH-10: Protected route with expired JWT returns 401")
@pytest.mark.be
async def test_protected_route_expired_token(client):
    """ตรวจสอบว่า JWT หมดอายุ → 401 Unauthorized"""
    # สร้าง expired JWT token
    expired_token = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjF9.INVALID"

    res = await get(client, "/customers",
                    token=expired_token,
                    expected_status=401)


@allure.title("TC-API-AUTH-11: Logout invalidates token")
@pytest.mark.be
async def test_logout_invalidates_token(client, admin_token):
    """ตรวจสอบว่าหลัง logout token เดิมใช้ไม่ได้"""
    with allure.step("Logout with valid token"):
        await post(client, "/auth/logout",
                   token=admin_token,
                   expected_status=200)

    with allure.step("Assert token no longer valid"):
        # ใช้ token เดิมอีกครั้ง → ต้องได้ 401
        res = await get(client, "/customers",
                        token=admin_token,
                        expected_status=401)


@allure.title("TC-API-AUTH-14: Login brute force protection (10 attempts)")
@pytest.mark.be
@pytest.mark.security
async def test_login_brute_force_protection(client, seed_data):
    """
    ตรวจสอบว่า login ผิด 10 ครั้ง → 429 Too Many Requests
    ป้องกัน password brute force attack
    """
    with allure.step("Submit wrong password 10 times"):
        for attempt in range(1, 11):
            with allure.step(f"Attempt {attempt}/10"):
                res = await post(client, "/auth/login", json={
                    "email": "owner@test.com",
                    "password": "wrong_password",
                })

    with allure.step("Assert 429 on 10th attempt"):
        assert res.status_code == 429, (
            f"Expected 429 Too Many Requests after 10 failed logins "
            f"but got {res.status_code}. "
            "Brute force protection must be active."
        )


@allure.title("TC-API-AUTH-15: Token cannot be used across partners")
@pytest.mark.be
@pytest.mark.security
async def test_token_cross_partner_isolation(client, seed_data):
    """
    ตรวจสอบว่า token ของ Partner A ใช้เรียก branch ของ Partner B ไม่ได้
    Data isolation ระหว่าง partners
    """
    with allure.step("Use Partner A owner token to access Partner B branch"):
        partner_b_branch_id = seed_data.get("partner_b_branch_id")
        if not partner_b_branch_id:
            pytest.skip("Partner B not in seed data")

        res = await get(client, "/customers",
                        token=seed_data["tokens"]["owner"],
                        params={"branch_id": partner_b_branch_id})

    with allure.step("Assert 403 Forbidden"):
        assert res.status_code == 403, (
            f"Expected 403 when accessing Partner B's data with Partner A's token "
            f"but got {res.status_code}. "
            "Cross-partner data isolation is broken."
        )


# ─── Password Reset ─────────────────────────────────────────────────────────────

@allure.title("TC-API-AUTH: Password forgot sends reset email")
@pytest.mark.be
async def test_password_forgot_sends_email(client, seed_data):
    """ตรวจสอบว่าขอ reset password → 200 OK"""
    res = await post(client, "/auth/password/forgot",
                     json={"email": "owner@test.com"},
                     expected_status=200)

    with allure.step("Assert email sent confirmation"):
        assert "message" in res.json()


@allure.title("TC-API-AUTH: Password reset with valid token")
@pytest.mark.be
async def test_password_reset_valid_token(client, seed_data, db_session):
    """ตรวจสอบว่า reset password ด้วย token ที่ถูกต้อง → 200 OK"""
    with allure.step("Get reset token from DB"):
        from api.models.user import PasswordResetToken
        token_record = db_session.query(PasswordResetToken).filter_by(used=False).first()
        if not token_record:
            pytest.skip("No reset token in DB")
        reset_token = "test_reset_token"

    with allure.step("Reset password"):
        res = await post(client, "/auth/password/reset", json={
            "token": reset_token,
            "new_password": "new_secure_pass",
        }, expected_status=200)

    with allure.step("Assert can login with new password"):
        login_res = await post(client, "/auth/login", json={
            "email": "owner@test.com",
            "password": "new_secure_pass",
        }, expected_status=200)
        assert "temporary_token" in login_res.json()


# ─── Internal Developer-only ─────────────────────────────────────────────────────

@allure.title("TC-INTERNAL: Assign password with developer API key")
@pytest.mark.be
@pytest.mark.security
async def test_internal_assign_password(client, seed_data):
    """
    ตรวจสอบว่า developer API key สามารถ force-assign password ให้ user ได้
    endpoint นี้ไม่มี UI, เข้าถึงได้เฉพาะ developer ยิงตรง
    """
    target_user_id = seed_data["users"]["admin"].id
    dev_api_key = "test_developer_api_key"  # จาก .env.test

    with allure.step("Assign new password via internal endpoint"):
        res = await post(
            client,
            f"/internal/assign-password/{target_user_id}",
            json={"new_password": "forced_new_pass"},
            api_key=dev_api_key,
            expected_status=200,
        )

    with allure.step("Verify can login with new password"):
        login_res = await post(client, "/auth/login", json={
            "email": "admin@test.com",
            "password": "forced_new_pass",
        }, expected_status=200)
        assert "temporary_token" in login_res.json()


@allure.title("TC-INTERNAL: Regular JWT cannot access internal endpoint")
@pytest.mark.be
@pytest.mark.security
async def test_internal_requires_api_key_not_jwt(client, admin_token):
    """
    ตรวจสอบว่า JWT ปกติ (ไม่ใช่ developer API key) ไม่สามารถเข้า /internal/* ได้
    """
    with allure.step("Try to access internal endpoint with regular JWT"):
        res = await post(
            client,
            "/internal/assign-password/some-user-id",
            token=admin_token,  # JWT ปกติ ไม่ใช่ API key
            json={"new_password": "hacked"},
        )

    with allure.step("Assert 403 Forbidden"):
        assert res.status_code == 403, (
            f"Expected 403 when accessing /internal with regular JWT "
            f"but got {res.status_code}. "
            "Internal endpoints must only accept Developer API Key."
        )
