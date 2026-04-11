# tests/be/test_cancel_policy_api.py
#
# BE tests สำหรับ Cancel Policy Settings API
# TC-API-CANCEL-01 ถึง TC-API-CANCEL-03

import pytest
import allure
from helpers.common_api import (
    get, put,
    assert_forbidden,
)


@allure.title("TC-API-CANCEL-01: GET /settings/cancel-policy — returns current policy")
@pytest.mark.be
async def test_get_cancel_policy_returns_current_settings(client, owner_token):
    """ตรวจสอบว่า GET /settings/cancel-policy คืน policy ปัจจุบัน"""
    response = await get(client, "/settings/cancel-policy",
                         token=owner_token, expected_status=200)

    with allure.step("Assert cancel policy fields present"):
        policy_data = response.json()
        assert "hours_before" in policy_data, (
            "Cancel policy must contain 'hours_before' field."
        )
        assert "return_hour" in policy_data, (
            "Cancel policy must contain 'return_hour' boolean field."
        )
        assert isinstance(policy_data["return_hour"], bool), (
            "'return_hour' must be a boolean value."
        )


@allure.title("TC-API-CANCEL-02: PUT /settings/cancel-policy — owner can update policy")
@pytest.mark.be
async def test_owner_can_update_cancel_policy(client, owner_token):
    """ตรวจสอบว่า owner อัปเดต cancel policy ได้ → 200 OK"""
    updated_policy_payload = {
        "hours_before": 12,
        "return_hour": False,
    }

    response = await put(client, "/settings/cancel-policy",
                         token=owner_token,
                         json=updated_policy_payload,
                         expected_status=200)

    with allure.step("Assert policy updated in response"):
        policy_data = response.json()
        assert policy_data.get("hours_before") == 12, (
            f"Expected hours_before=12 but got {policy_data.get('hours_before')}."
        )
        assert policy_data.get("return_hour") is False, (
            "Expected return_hour=False after update."
        )


@allure.title("TC-API-CANCEL-03: PUT /settings/cancel-policy — admin cannot update policy")
@pytest.mark.be
async def test_admin_cannot_update_cancel_policy(client, admin_token):
    """ตรวจสอบว่า admin แก้ไข cancel policy ไม่ได้ → 403 Forbidden"""
    response = await put(client, "/settings/cancel-policy",
                         token=admin_token,
                         json={"hours_before": 6, "return_hour": True})

    assert_forbidden(response)
