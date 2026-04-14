# tests/be/test_auth_api.py
#
# BE tests สำหรับ Authentication API
# TC-API-AUTH-01 ถึง TC-API-AUTH-15

import pytest
import allure
from datetime import datetime, timedelta
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
@pytest.mark.isolated_last
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


# ─── AUTH-18: Temporary Token Cannot Access Protected Routes ─────────────────────

@allure.title("TC-API-AUTH-18: Temporary token (pre-PIN) returns 401 on protected routes")
@pytest.mark.be
@pytest.mark.security
async def test_temporary_token_rejected_on_protected_route(client, seed_data):
    """
    ตรวจสอบว่า temporary_token ที่ได้หลัง login (ก่อน verify PIN)
    ไม่สามารถใช้เรียก protected endpoints ได้ → ต้องได้ 401
    """
    with allure.step("Login to obtain temporary token (pre-PIN)"):
        login_response = await post(client, "/auth/login", json={
            "email": "owner@test.com",
            "password": "test_pass",
        }, expected_status=200)
        temporary_token = login_response.json()["temporary_token"]

    with allure.step("Use temporary token to call protected endpoint"):
        protected_response = await get(
            client, "/customers",
            token=temporary_token,
        )

    with allure.step("Assert 401 — temporary token must not grant resource access"):
        assert protected_response.status_code == 401, (
            f"Expected 401 when using temporary (pre-PIN) token on protected route "
            f"but got {protected_response.status_code}. "
            "Temporary tokens must only be used for PIN verification, "
            "not for accessing protected resources."
        )


# ─── AUTH-20: Password Forgot — Unknown Email Returns 200 ────────────────────────

@allure.title("TC-API-AUTH-20: Password forgot with unknown email returns 200 (security)")
@pytest.mark.be
@pytest.mark.security
async def test_password_forgot_unknown_email_returns_200(client):
    """
    ตรวจสอบว่า forgot password ด้วย email ที่ไม่มีในระบบ → ได้ 200 เหมือนกัน
    ป้องกัน email enumeration attack — ระบบต้องไม่เปิดเผยว่า email มีอยู่หรือไม่
    """
    with allure.step("Submit forgot password with unknown email"):
        response = await post(client, "/auth/password/forgot", json={
            "email": "nobody_unknown@test.com",
        })

    with allure.step("Assert 200 OK — response must be identical regardless of email existence"):
        assert response.status_code == 200, (
            f"Expected 200 OK for unknown email in forgot password "
            f"but got {response.status_code}. "
            "Returning different status for unknown emails enables email enumeration attacks."
        )


# ─── AUTH-22: Password Reset — Expired Token ─────────────────────────────────────

@allure.title("TC-API-AUTH-22: Password reset with expired token returns 400")
@pytest.mark.be
async def test_password_reset_expired_token_returns_400(client):
    """
    ตรวจสอบว่า reset password ด้วย token ที่หมดอายุ → 400 Bad Request
    """
    with allure.step("Submit reset with known-expired token"):
        response = await post(client, "/auth/password/reset", json={
            "token": "expired_or_invalid_reset_token",
            "new_password": "NewPass123",
        })

    with allure.step("Assert 400 Bad Request"):
        assert response.status_code == 400, (
            f"Expected 400 for expired reset token but got {response.status_code}. "
            "Expired reset tokens must be rejected."
        )
        error_detail = response.json().get("detail", "")
        assert "expired" in error_detail.lower() or "invalid" in error_detail.lower(), (
            f"Error detail must mention 'expired' or 'invalid' but got: '{error_detail}'"
        )


# ─── AUTH-23 & AUTH-24: Password Change While Logged In ──────────────────────────

@allure.title("TC-API-AUTH-23: Change password while logged in — success")
@pytest.mark.be
async def test_password_change_while_logged_in(client, admin_token):
    """
    ตรวจสอบว่า user ที่ login แล้วสามารถเปลี่ยน password ตัวเองได้
    """
    with allure.step("Change password with correct old password"):
        response = await post(client, "/auth/password/change",
                              token=admin_token,
                              json={
                                  "old_password": "test_pass",
                                  "new_password": "NewSecurePass456",
                              }, expected_status=200)

    with allure.step("Assert 200 OK — password changed successfully"):
        assert response.status_code == 200, (
            f"Expected 200 OK for valid password change but got {response.status_code}."
        )


@allure.title("TC-API-AUTH-24: Change password with wrong old password returns 401")
@pytest.mark.be
async def test_password_change_wrong_old_password(client, admin_token):
    """
    ตรวจสอบว่า เปลี่ยน password ด้วย old_password ผิด → 401 Unauthorized
    """
    with allure.step("Submit password change with wrong old password"):
        response = await post(client, "/auth/password/change",
                              token=admin_token,
                              json={
                                  "old_password": "wrong_old_password",
                                  "new_password": "NewPass123",
                              })

    with allure.step("Assert 401 Unauthorized"):
        assert response.status_code == 401, (
            f"Expected 401 when old password is wrong but got {response.status_code}. "
            "Password change must verify the current password before allowing update."
        )


# ─── AUTH-26: Internal Assign PIN ────────────────────────────────────────────────

@allure.title("TC-API-AUTH-26: Developer API key can assign PIN and unlock account")
@pytest.mark.be
@pytest.mark.security
@pytest.mark.isolated_last
async def test_internal_assign_pin(client, seed_data):
    """
    ตรวจสอบว่า developer API key สามารถ force-assign PIN และ unlock account ได้
    ใช้ในกรณี admin/support ต้องการ reset PIN โดยตรง
    """
    target_user_id = seed_data["users"]["admin"].id
    developer_api_key = "test_developer_api_key"

    with allure.step("Assign new PIN via internal endpoint"):
        response = await post(
            client,
            f"/internal/assign-pin/{target_user_id}",
            json={"new_pin": "999999"},
            api_key=developer_api_key,
            expected_status=200,
        )

    with allure.step("Assert PIN assigned and account unlocked"):
        response_data = response.json()
        assert response_data is not None, "Response must not be empty"

    with allure.step("Verify new PIN works for login flow"):
        login_response = await post(client, "/auth/login", json={
            "email": "admin@test.com",
            "password": "test_pass",
        }, expected_status=200)
        temporary_token = login_response.json()["temporary_token"]

        pin_response = await post(client, "/auth/pin/verify",
                                  token=temporary_token,
                                  json={"pin": "999999"},
                                  expected_status=200)
        assert "access_token" in pin_response.json(), (
            "New PIN must work after internal assign-pin. "
            "If PIN verify fails, the assign-pin endpoint did not persist the change."
        )


# ─── Dual-Session Tests ───────────────────────────────────────────────────────

@allure.title("TC-API-AUTH-DS-01: Login returns opaque token and creates password_sessions row")
@pytest.mark.be
async def test_login_returns_opaque_token_and_creates_db_row(client, seed_data, db_session):
    """Login must return opaque token (not JWT), and create a password_sessions row"""
    res = await post(client, "/auth/login", json={
        "email": "owner@test.com", "password": "test_pass"
    }, expected_status=200)
    data = res.json()

    # Assert: response has password_session_token (opaque — not 3 JWT parts)
    token = data.get("password_session_token") or data.get("temporary_token")
    assert token, "Response must contain password_session_token"
    assert len(token.split(".")) != 3, "password_session_token must NOT be a JWT (no 3-part dot format)"
    assert data.get("expires_in"), "Response must contain expires_in"

    # Assert: DB row created
    from api.models.user import PasswordSession
    owner = seed_data["users"]["owner"]
    rows = db_session.query(PasswordSession).filter_by(user_id=owner.id, is_active=True).all()
    assert len(rows) >= 1, "password_sessions row must be created after login"
    row = rows[-1]
    assert row.expires_at > datetime.utcnow(), "expires_at must be in the future"


@allure.title("TC-API-AUTH-DS-02: PIN verify returns 6h access JWT and creates UserSession")
@pytest.mark.be
async def test_pin_verify_returns_6h_jwt(client, seed_data, db_session, password_session_via_login):
    """PIN verify with valid opaque token must return 6h access JWT"""
    from jose import jwt as pyjwt
    from api.models.user import UserSession

    res = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token=password_session_via_login["token"],
        expected_status=200)
    data = res.json()

    assert "access_token" in data, "Response must contain access_token"
    assert data.get("expires_in"), "Response must contain expires_in"
    assert data.get("token_type") == "bearer"

    # Assert: JWT exp is ~6 hours from now
    import time
    payload = pyjwt.decode(
        data["access_token"],
        key="",
        options={"verify_signature": False, "verify_exp": False},
    )
    exp = payload.get("exp", 0)
    now = int(time.time())
    remaining_hours = (exp - now) / 3600
    assert 5.5 <= remaining_hours <= 6.5, f"JWT must expire ~6h from now, got {remaining_hours:.1f}h remaining"
    assert payload.get("pin_verified") is True

    # Assert: UserSession row created
    owner = seed_data["users"]["owner"]
    sessions = db_session.query(UserSession).filter_by(user_id=owner.id, is_active=True).all()
    assert len(sessions) >= 1, "UserSession must be created after PIN verify"


@allure.title("TC-API-AUTH-DS-03: Re-enter PIN with valid opaque after 6h expiry returns new JWT")
@pytest.mark.be
async def test_reenter_pin_with_valid_password_session(client, seed_data, password_session_via_login):
    """Opaque password token can be reused to get a new access JWT (simulates 6h expiry scenario)"""
    # Get first access JWT
    res1 = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token=password_session_via_login["token"],
        expected_status=200)
    jwt1 = res1.json()["access_token"]

    # Get second access JWT using same opaque (simulates re-PIN after 6h)
    res2 = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token=password_session_via_login["token"],
        expected_status=200)
    jwt2 = res2.json()["access_token"]

    assert jwt1 != jwt2, "Second PIN verify must return a new (different) JWT"


@allure.title("TC-API-AUTH-DS-04: Expired password session returns 401 session_expired")
@pytest.mark.be
async def test_expired_password_session_returns_401(client, seed_data, db_session):
    """Manually expire a password session row → pin/verify must return 401 session_expired"""
    from api.models.user import PasswordSession
    import hashlib, secrets

    # Create a manually expired password session
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    owner = seed_data["users"]["owner"]
    expired_session = PasswordSession(
        user_id=owner.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() - timedelta(hours=1),  # expired 1h ago
        is_active=True,
    )
    db_session.add(expired_session)
    db_session.flush()

    res = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token=raw_token,
        expected_status=401)

    data = res.json()
    error_code = data.get("detail", {}).get("error_code") if isinstance(data.get("detail"), dict) else data.get("error_code")
    assert error_code == "session_expired", f"Expected session_expired, got {data}"


@allure.title("TC-API-AUTH-DS-05: Wrong PIN returns 401 invalid_pin (not session_expired)")
@pytest.mark.be
async def test_wrong_pin_returns_invalid_pin_error_code(client, seed_data, password_session_via_login):
    """Wrong PIN must return error_code=invalid_pin, not session_expired"""
    res = await post(client, "/auth/pin/verify",
        json={"pin": "000000"},  # wrong PIN
        token=password_session_via_login["token"],
        expected_status=401)

    data = res.json()
    detail = data.get("detail")
    # error_code could be in detail dict or top-level
    if isinstance(detail, dict):
        error_code = detail.get("error_code")
    else:
        error_code = data.get("error_code") or detail

    assert error_code in ("invalid_pin", "Invalid PIN"), f"Expected invalid_pin, got: {data}"


@allure.title("TC-API-AUTH-DS-06: Protected route rejects opaque token (must be JWT)")
@pytest.mark.be
async def test_protected_route_rejects_opaque_token(client, seed_data, password_session_via_login):
    """Opaque password token must NOT be accepted on protected routes (JWT only)"""
    res = await get(client, "/auth/me",
        token=password_session_via_login["token"],
        expected_status=401)
    assert res.status_code == 401, "Protected route must reject opaque token"


@allure.title("TC-API-AUTH-DS-07: Logout invalidates all password sessions")
@pytest.mark.be
async def test_logout_invalidates_all_password_sessions(client, seed_data, db_session, full_auth_via_api):
    """After logout, password_sessions for user must all be is_active=False"""
    from api.models.user import PasswordSession
    password_token, access_jwt = full_auth_via_api

    # Logout using access JWT
    await post(client, "/auth/logout", token=access_jwt, expected_status=200)

    # Assert: all password_sessions for owner are inactive
    owner = seed_data["users"]["owner"]
    active_sessions = db_session.query(PasswordSession).filter_by(
        user_id=owner.id, is_active=True
    ).all()
    assert len(active_sessions) == 0, "All password_sessions must be inactive after logout"

    # Assert: opaque token no longer works
    res = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token=password_token,
        expected_status=401)
    assert res.status_code == 401, "Password session must be revoked after logout"


@allure.title("TC-API-AUTH-DS-08: Password change invalidates all sessions")
@pytest.mark.be
@pytest.mark.isolated_last
async def test_password_change_invalidates_all_sessions(client, seed_data, db_session, full_auth_via_api):
    """After password change, all password_sessions and UserSessions must be revoked"""
    from api.models.user import PasswordSession, UserSession
    password_token, access_jwt = full_auth_via_api
    owner = seed_data["users"]["owner"]

    # Change password
    await post(client, "/auth/password/change",
        token=access_jwt,
        json={"old_password": "test_pass", "new_password": "new_test_pass_123"},
        expected_status=200)

    # Assert: all password_sessions inactive
    active_ps = db_session.query(PasswordSession).filter_by(user_id=owner.id, is_active=True).all()
    assert len(active_ps) == 0, "All password_sessions must be revoked after password change"

    # Assert: opaque token no longer works
    res2 = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token=password_token,
        expected_status=401)
    assert res2.status_code == 401


@allure.title("TC-API-AUTH-DS-09: Revoked password session returns 401 session_revoked")
@pytest.mark.be
async def test_revoked_password_session_returns_401(client, seed_data, db_session):
    """Manually revoke a password session → pin/verify must return 401"""
    from api.models.user import PasswordSession
    import hashlib, secrets

    # Create a revoked (is_active=False) password session
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    owner = seed_data["users"]["owner"]
    revoked_session = PasswordSession(
        user_id=owner.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=30),
        is_active=False,  # revoked
    )
    db_session.add(revoked_session)
    db_session.flush()

    res = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token=raw_token,
        expected_status=401)
    assert res.status_code == 401


@allure.title("TC-API-AUTH-DS-10: PIN verify with completely unknown token returns 401")
@pytest.mark.be
async def test_unknown_token_returns_401(client, seed_data):
    """Completely unknown token must return 401 (not 500)"""
    res = await post(client, "/auth/pin/verify",
        json={"pin": "123456"},
        token="totally_unknown_token_xyz123",
        expected_status=401)
    assert res.status_code == 401
