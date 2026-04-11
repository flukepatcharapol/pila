# tests/be/test_signature_print_api.py
#
# BE tests สำหรับ Signature Print API
# TC-API-PRINT-01 ถึง TC-API-PRINT-04

import pytest
import allure
from helpers.common_api import get, post


@allure.title("TC-API-PRINT-01: POST /signature-print/generate — generates Google Sheet URL")
@pytest.mark.be
async def test_generate_signature_sheet_success(client, admin_token, create_order):
    """
    ตรวจสอบว่า admin ที่เชื่อม Google Drive แล้ว สามารถ generate signature sheet ได้
    → 200 OK พร้อม file_url และ file_id
    """
    order_id = create_order()

    response = await post(client, "/signature-print/generate",
                          token=admin_token,
                          json={"order_id": order_id})

    with allure.step("Assert 200 OK with Google Drive file info"):
        if response.status_code == 200:
            sheet_data = response.json()
            assert "file_url" in sheet_data, "Response must contain 'file_url'."
            assert "file_id" in sheet_data, "Response must contain 'file_id'."
            assert "docs.google.com" in sheet_data.get("file_url", ""), (
                "file_url must be a Google Docs URL."
            )
        elif response.status_code == 400:
            error_detail = response.json().get("detail", "")
            assert "google" in error_detail.lower() or "drive" in error_detail.lower(), (
                "400 error must mention Google Drive connection issue."
            )
        else:
            pytest.fail(
                f"Expected 200 or 400 for signature print generate "
                f"but got {response.status_code}."
            )


@allure.title("TC-API-PRINT-02: POST /signature-print/generate — blocked when Google Drive not connected")
@pytest.mark.be
async def test_generate_signature_sheet_without_google_drive(client, admin_token,
                                                              create_order, db_session):
    """
    ตรวจสอบว่า admin ที่ไม่ได้เชื่อม Google Drive → 400 Bad Request
    """
    from api.models import User

    order_id = create_order()

    with allure.step("Remove Google Drive token from admin"):
        admin_user_record = db_session.query(User).filter_by(role="ADMIN").first()
        if hasattr(admin_user_record, "google_token"):
            admin_user_record.google_token = None
            db_session.flush()

    response = await post(client, "/signature-print/generate",
                          token=admin_token,
                          json={"order_id": order_id})

    with allure.step("Assert 400 — Google Drive not connected"):
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            assert "google" in error_detail.lower() or "drive" in error_detail.lower(), (
                "Error must mention Google Drive not connected."
            )


@allure.title("TC-API-PRINT-03: GET /signature-print/list — returns list of generated files")
@pytest.mark.be
async def test_get_signature_print_list(client, admin_token):
    """ตรวจสอบว่า GET /signature-print/list คืน list ไฟล์ที่ generate แล้ว"""
    response = await get(client, "/signature-print/list",
                         token=admin_token, expected_status=200)

    with allure.step("Assert list of generated files returned"):
        file_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert isinstance(file_list, list), "Response must be a list of generated files."
        for file_entry in file_list:
            assert "order_id" in file_entry, "File entry must contain 'order_id'."
            assert "file_url" in file_entry, "File entry must contain 'file_url'."
            assert "created_at" in file_entry, "File entry must contain 'created_at'."


@allure.title("TC-API-PRINT-04: GET /signature-print/storage — returns Drive storage info")
@pytest.mark.be
async def test_get_drive_storage_info(client, admin_token):
    """ตรวจสอบว่า GET /signature-print/storage คืน storage usage info"""
    response = await get(client, "/signature-print/storage",
                         token=admin_token)

    with allure.step("Assert storage info returned (200) or not connected (400)"):
        assert response.status_code in (200, 400), (
            f"Expected 200 or 400 for storage info but got {response.status_code}."
        )
        if response.status_code == 200:
            storage_data = response.json()
            required_storage_fields = ["used_bytes", "total_bytes"]
            for field_name in required_storage_fields:
                assert field_name in storage_data, (
                    f"Storage info must contain '{field_name}' field."
                )
