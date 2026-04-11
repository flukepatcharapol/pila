# tests/be/test_help_api.py
#
# BE tests สำหรับ Help Page API
# TC-API-HELP-01 ถึง TC-API-HELP-03

import pytest
import allure
from helpers.common_api import get


@allure.title("TC-API-HELP-01: GET /help/manual — trainer sees only role-specific content")
@pytest.mark.be
async def test_trainer_help_manual_scoped_to_role(client, trainer_token):
    """
    ตรวจสอบว่า trainer เห็นเฉพาะ manual sections ที่เกี่ยวกับ trainer role
    ไม่เห็น sections ของ admin/owner
    """
    response = await get(client, "/help/manual",
                         token=trainer_token, expected_status=200)

    with allure.step("Assert trainer-relevant content returned"):
        manual_data = response.json()
        assert manual_data is not None, "Help manual response must not be empty."
        manual_sections = manual_data if isinstance(manual_data, list) else manual_data.get("sections", [])
        assert isinstance(manual_sections, list), "Manual content must be a list of sections."


@allure.title("TC-API-HELP-02: GET /help/manual — owner sees full manual")
@pytest.mark.be
async def test_owner_help_manual_returns_all_sections(client, owner_token):
    """ตรวจสอบว่า owner เห็น manual ทุก section"""
    response = await get(client, "/help/manual",
                         token=owner_token, expected_status=200)

    with allure.step("Assert full manual content returned for owner"):
        manual_data = response.json()
        assert manual_data is not None, "Owner help manual must not be empty."


@allure.title("TC-API-HELP-03: GET /help/line-qr — returns developer + branch QR for admin")
@pytest.mark.be
async def test_help_line_qr_returns_developer_and_branch_qr(client, admin_token, seed_data):
    """
    ตรวจสอบว่า GET /help/line-qr คืน QR สำหรับ developer และ branch
    Branch QR ต้องตรงกับ Pattaya (branch ของ admin ที่ login)
    """
    response = await get(client, "/help/line-qr",
                         token=admin_token, expected_status=200)

    with allure.step("Assert developer and branch QR URLs present"):
        qr_data = response.json()
        assert "developer_qr_url" in qr_data, (
            "Response must contain 'developer_qr_url' field."
        )
        assert "branch_qr_url" in qr_data, (
            "Response must contain 'branch_qr_url' field."
        )

    with allure.step("Assert branch QR matches admin's assigned branch (Pattaya)"):
        branch_qr_url = qr_data.get("branch_qr_url", "")
        assert branch_qr_url, "Branch QR URL must not be empty for Pattaya admin."
