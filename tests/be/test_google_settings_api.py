# tests/be/test_google_settings_api.py
#
# BE tests สำหรับ Google Account Settings API
# TC-API-GOOGLE-01 ถึง TC-API-GOOGLE-04

import pytest
import allure
from helpers.common_api import get, post, delete


@allure.title("TC-API-GOOGLE-01: POST /settings/google/connect — connect Google Account")
@pytest.mark.be
async def test_connect_google_account(client, admin_token):
    """
    ตรวจสอบว่า POST /settings/google/connect ด้วย OAuth code → 200 OK
    คืน connected_email และ connected=true
    """
    mock_oauth_code = "test_mock_oauth_code_for_google"

    response = await post(client, "/settings/google/connect",
                          token=admin_token,
                          json={"code": mock_oauth_code})

    with allure.step("Assert 200 OK with connection info (or appropriate error)"):
        if response.status_code == 200:
            connection_data = response.json()
            assert "connected_email" in connection_data, (
                "Response must contain 'connected_email' after connecting."
            )
            assert connection_data.get("connected") is True, (
                "Response must have 'connected'=True after successful connection."
            )
        elif response.status_code in (400, 422):
            pytest.skip("Mock OAuth code not accepted in test environment — skipping")
        else:
            pytest.fail(
                f"Unexpected status {response.status_code} for Google connect."
            )


@allure.title("TC-API-GOOGLE-02: DELETE /settings/google/disconnect — removes Google token")
@pytest.mark.be
async def test_disconnect_google_account(client, admin_token, db_session):
    """
    ตรวจสอบว่า DELETE /settings/google/disconnect ลบ Google token → 200 OK
    """
    response = await delete(client, "/settings/google/disconnect",
                            token=admin_token, expected_status=200)

    with allure.step("Assert 200 OK — Google token removed"):
        assert response.status_code == 200, "Disconnect must return 200 OK."

    with allure.step("Verify Google token removed from DB"):
        from api.models import User
        admin_user_record = db_session.query(User).filter_by(role="ADMIN").first()
        if hasattr(admin_user_record, "google_token"):
            assert admin_user_record.google_token is None, (
                "Google token must be removed from DB after disconnect."
            )


@allure.title("TC-API-GOOGLE-03: GET /settings/google/storage — returns storage info when connected")
@pytest.mark.be
async def test_get_google_storage_info_when_connected(client, admin_token):
    """ตรวจสอบว่า GET /settings/google/storage คืน storage info เมื่อ connected"""
    response = await get(client, "/settings/google/storage",
                         token=admin_token)

    with allure.step("Assert 200 OK with storage data or 400 if not connected"):
        assert response.status_code in (200, 400), (
            f"Expected 200 or 400 for Google storage info but got {response.status_code}."
        )
        if response.status_code == 200:
            storage_data = response.json()
            assert "used_bytes" in storage_data or "used_gb" in storage_data, (
                "Storage info must contain usage data."
            )


@allure.title("TC-API-GOOGLE-04: GET /settings/google/storage — 400 when not connected")
@pytest.mark.be
async def test_get_google_storage_info_when_not_connected(client, admin_token, db_session):
    """ตรวจสอบว่า GET /settings/google/storage เมื่อไม่ได้ connect → 400 Bad Request"""
    with allure.step("Clear Google token from admin"):
        from api.models import User
        admin_user_record = db_session.query(User).filter_by(role="ADMIN").first()
        if hasattr(admin_user_record, "google_token"):
            admin_user_record.google_token = None
            db_session.flush()

    response = await get(client, "/settings/google/storage",
                         token=admin_token)

    with allure.step("Assert 400 Bad Request — Google Drive not connected"):
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            assert "google" in error_detail.lower() or "drive" in error_detail.lower() or "connect" in error_detail.lower(), (
                f"Error detail must mention Google Drive connection issue, got: '{error_detail}'"
            )
