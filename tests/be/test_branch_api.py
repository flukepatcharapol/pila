# tests/be/test_branch_api.py
#
# BE tests สำหรับ Branch Config API
# TC-API-BRANCH-01 ถึง TC-API-BRANCH-06

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_forbidden, assert_conflict,
)


@allure.title("TC-API-BRANCH-01: GET /branches — returns all branches with required fields")
@pytest.mark.be
async def test_branch_list_returns_all_branches(client, admin_token, seed_data):
    """ตรวจสอบว่า GET /branches คืน list ทุก branch พร้อม fields ครบถ้วน"""
    response = await get(client, "/branches", token=admin_token, expected_status=200)

    with allure.step("Assert at least 3 branches returned with required fields"):
        branch_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert len(branch_list) >= 3, "At least 3 branches must be returned."
        required_branch_fields = ["name", "prefix"]
        for branch_data in branch_list:
            for field_name in required_branch_fields:
                assert field_name in branch_data, (
                    f"Branch must contain '{field_name}' field."
                )


@allure.title("TC-API-BRANCH-02: PUT /branches/:id — owner can update branch")
@pytest.mark.be
async def test_owner_can_update_branch(client, owner_token, seed_data):
    """ตรวจสอบว่า owner แก้ไข branch config ได้ → 200 OK"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    update_payload = {
        "opening_time": "08:00",
        "closing_time": "22:00",
    }

    response = await put(client, f"/branches/{pattaya_branch_id}",
                         token=owner_token,
                         json=update_payload,
                         expected_status=200)

    with allure.step("Assert branch updated successfully"):
        branch_data = response.json()
        assert branch_data.get("opening_time") == "08:00", (
            "Branch opening_time must be updated to 08:00."
        )


@allure.title("TC-API-BRANCH-03: PUT /branches/:id — admin cannot update branch")
@pytest.mark.be
async def test_admin_cannot_update_branch(client, admin_token, seed_data):
    """ตรวจสอบว่า admin แก้ไข branch config ไม่ได้ → 403 Forbidden"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    response = await put(client, f"/branches/{pattaya_branch_id}",
                         token=admin_token,
                         json={"opening_time": "07:00"})

    assert_forbidden(response)


@allure.title("TC-API-BRANCH-04: POST /branches — owner creates new branch")
@pytest.mark.be
async def test_owner_creates_new_branch(client, owner_token):
    """ตรวจสอบว่า owner สร้าง branch ใหม่ได้ → 201 Created"""
    new_branch_payload = {
        "name": "Bangkok",
        "prefix": "BKK",
        "source_types": [{"label": "Page", "code": "MKT"}],
        "opening_time": "09:00",
        "closing_time": "21:00",
    }

    response = await post(client, "/branches",
                          token=owner_token,
                          json=new_branch_payload,
                          expected_status=201)

    with allure.step("Assert new branch created"):
        branch_data = response.json()
        assert branch_data.get("prefix") == "BKK", (
            "New branch must have the specified prefix 'BKK'."
        )


@allure.title("TC-API-BRANCH-05: POST /branches — admin cannot create branch")
@pytest.mark.be
async def test_admin_cannot_create_branch(client, admin_token):
    """ตรวจสอบว่า admin สร้าง branch ไม่ได้ → 403 Forbidden"""
    response = await post(client, "/branches",
                          token=admin_token,
                          json={"name": "Forbidden Branch", "prefix": "FBD"})

    assert_forbidden(response)


@allure.title("TC-API-BRANCH-06: PUT /branches/:id — update source type updates customer code prefix")
@pytest.mark.be
async def test_update_source_type_affects_customer_code(client, owner_token,
                                                         admin_token, seed_data):
    """
    ตรวจสอบว่าเมื่ออัปเดต source type code ใน branch
    customer ที่สร้างใหม่จะใช้ code ใหม่
    """
    pattaya_branch_id = str(seed_data["pattaya"].id)
    mkt_source_type = seed_data["source_types"]["BPY_MKT"]

    with allure.step("Update source type code from MKT to PTY"):
        await put(client, f"/branches/{pattaya_branch_id}",
                  token=owner_token,
                  json={
                      "source_types": [{"id": str(mkt_source_type.id), "code": "PTY"}]
                  },
                  expected_status=200)

    with allure.step("Create customer with updated source type"):
        customer_payload = {
            "branch_id": pattaya_branch_id,
            "source_type_id": str(mkt_source_type.id),
            "first_name": "Code Test",
            "last_name": "Customer",
            "phone": "0812345678",
            "status": "ACTIVE",
        }
        response = await post(client, "/customers",
                              token=admin_token,
                              json=customer_payload,
                              expected_status=201)

    with allure.step("Assert customer code uses new prefix PTY"):
        customer_data = response.json()
        customer_code = customer_data.get("customer_code", "")
        assert "PTY" in customer_code, (
            f"Customer code '{customer_code}' must contain 'PTY' after source type update. "
            "Code generation must use the updated source type code."
        )
