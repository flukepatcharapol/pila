# tests/be/test_caretaker_api.py
#
# BE tests สำหรับ Caretaker API
# TC-API-CARE-01 ถึง TC-API-CARE-06

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_forbidden, assert_branch_scope,
)


@allure.title("TC-API-CARE-01: GET /caretakers — admin sees only own branch caretakers")
@pytest.mark.be
async def test_admin_sees_own_branch_caretakers_only(client, admin_token,
                                                      create_caretaker, seed_data):
    """ตรวจสอบว่า admin เห็นเฉพาะ caretaker ในสาขาตัวเอง"""
    pattaya_branch_id = str(seed_data["pattaya"].id)
    create_caretaker(branch="pattaya")
    create_caretaker(branch="kanchanaburi")

    response = await get(client, "/caretakers", token=admin_token, expected_status=200)

    with allure.step("Assert only Pattaya caretakers returned"):
        caretaker_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert_branch_scope(caretaker_list, expected_branch_id=pattaya_branch_id)


@allure.title("TC-API-CARE-02: GET /caretakers — owner sees all branches")
@pytest.mark.be
async def test_owner_sees_all_branch_caretakers(client, owner_token,
                                                 create_caretaker, seed_data):
    """ตรวจสอบว่า owner เห็น caretaker จากทุกสาขาใน partner"""
    create_caretaker(branch="pattaya")
    create_caretaker(branch="chachoengsao")

    response = await get(client, "/caretakers", token=owner_token, expected_status=200)

    with allure.step("Assert caretakers from multiple branches present"):
        caretaker_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        branch_id_set = {caretaker["branch_id"] for caretaker in caretaker_list}
        assert len(branch_id_set) >= 2, (
            f"Owner should see caretakers from multiple branches "
            f"but only saw {len(branch_id_set)} distinct branch(es)."
        )


@allure.title("TC-API-CARE-03: POST /caretakers — create valid caretaker")
@pytest.mark.be
async def test_create_caretaker_valid(client, admin_token, seed_data):
    """ตรวจสอบว่าสร้าง caretaker ด้วย payload ถูกต้อง → 201 Created"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    caretaker_payload = {
        "name": "New Test Caretaker",
        "email": "new_caretaker@test.com",
        "branch_id": pattaya_branch_id,
        "status": "ACTIVE",
    }

    response = await post(client, "/caretakers",
                          token=admin_token,
                          json=caretaker_payload,
                          expected_status=201)

    with allure.step("Assert caretaker created with correct branch"):
        caretaker_data = response.json()
        assert caretaker_data.get("branch_id") == pattaya_branch_id, (
            "Created caretaker must belong to the specified branch."
        )
        assert caretaker_data.get("status") == "ACTIVE"


@allure.title("TC-API-CARE-04: POST /caretakers — admin cannot create for other branch")
@pytest.mark.be
async def test_admin_cannot_create_caretaker_for_other_branch(client, admin_token, seed_data):
    """ตรวจสอบว่า admin สร้าง caretaker ในสาขาอื่น → 403 Forbidden"""
    kanchanaburi_branch_id = str(seed_data["kanchanaburi"].id)

    response = await post(client, "/caretakers",
                          token=admin_token,
                          json={
                              "name": "Cross Branch Caretaker",
                              "email": "cross@test.com",
                              "branch_id": kanchanaburi_branch_id,
                              "status": "ACTIVE",
                          })

    assert_forbidden(response)


@allure.title("TC-API-CARE-05: PUT /caretakers/:id — update caretaker info")
@pytest.mark.be
async def test_update_caretaker_info(client, admin_token, create_caretaker):
    """ตรวจสอบว่าอัปเดต caretaker info ได้ → 200 OK"""
    caretaker_id = create_caretaker(branch="pattaya")

    updated_name = "Updated Caretaker Name"
    response = await put(client, f"/caretakers/{caretaker_id}",
                         token=admin_token,
                         json={"name": updated_name, "status": "ACTIVE"},
                         expected_status=200)

    with allure.step("Assert name updated in response"):
        caretaker_data = response.json()
        assert caretaker_data.get("name") == updated_name, (
            f"Expected name='{updated_name}' after update "
            f"but got '{caretaker_data.get('name')}'."
        )


@allure.title("TC-API-CARE-06: DELETE /caretakers/:id — admin can delete caretaker")
@pytest.mark.be
async def test_delete_caretaker(client, admin_token, create_caretaker):
    """ตรวจสอบว่า admin ลบ caretaker ได้ → 204 No Content"""
    caretaker_id = create_caretaker(branch="pattaya")

    await delete(client, f"/caretakers/{caretaker_id}",
                 token=admin_token, expected_status=204)
