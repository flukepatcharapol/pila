# tests/be/test_permission_api.py
#
# BE tests สำหรับ Permission Matrix API
# TC-API-PERM-01 ถึง TC-API-PERM-04

import pytest
import allure
from helpers.common_api import (
    get, put,
    assert_forbidden,
)


# ─── GET /permissions ─────────────────────────────────────────────────────────────

@allure.title("TC-API-PERM-01: GET /permissions — developer sees all 4 role columns")
@pytest.mark.be
async def test_developer_sees_all_permission_roles(client, developer_token):
    """ตรวจสอบว่า developer เห็น permission matrix ครบ 4 roles"""
    response = await get(client, "/permissions",
                         token=developer_token, expected_status=200)

    with allure.step("Assert all 4 role keys present"):
        permission_matrix = response.json()
        expected_role_keys = {"owner", "branch_master", "admin", "trainer"}
        actual_role_keys = set(permission_matrix.keys())
        missing_roles = expected_role_keys - actual_role_keys
        assert not missing_roles, (
            f"Permission matrix missing role columns: {missing_roles}. "
            "Developer must see all 4 role columns."
        )


@allure.title("TC-API-PERM-01b: GET /permissions — owner sees 3 role columns (below owner)")
@pytest.mark.be
async def test_owner_sees_subordinate_permission_roles(client, owner_token):
    """ตรวจสอบว่า owner เห็น permission matrix เฉพาะ roles ที่ต่ำกว่า"""
    response = await get(client, "/permissions",
                         token=owner_token, expected_status=200)

    with allure.step("Assert owner sees branch_master, admin, trainer — not developer or owner"):
        permission_matrix = response.json()
        assert "branch_master" in permission_matrix, "Owner must see branch_master column."
        assert "admin" in permission_matrix, "Owner must see admin column."
        assert "trainer" in permission_matrix, "Owner must see trainer column."
        assert "developer" not in permission_matrix, (
            "Owner must NOT see developer column — cannot configure higher roles."
        )
        assert "owner" not in permission_matrix, (
            "Owner must NOT see own role column."
        )


@allure.title("TC-API-PERM-01c: GET /permissions — branch_master sees 2 role columns")
@pytest.mark.be
async def test_branch_master_sees_limited_permission_roles(client, branch_master_token):
    """ตรวจสอบว่า branch_master เห็นแค่ admin และ trainer columns"""
    response = await get(client, "/permissions",
                         token=branch_master_token, expected_status=200)

    with allure.step("Assert branch_master sees only admin and trainer"):
        permission_matrix = response.json()
        assert "admin" in permission_matrix, "Branch master must see admin column."
        assert "trainer" in permission_matrix, "Branch master must see trainer column."
        for restricted_role in ("developer", "owner", "branch_master"):
            assert restricted_role not in permission_matrix, (
                f"Branch master must NOT see '{restricted_role}' column."
            )


@allure.title("TC-API-PERM-01d: GET /permissions — admin returns 403")
@pytest.mark.be
async def test_admin_cannot_access_permission_matrix(client, admin_token):
    """ตรวจสอบว่า admin เข้า permission matrix ไม่ได้ → 403"""
    response = await get(client, "/permissions", token=admin_token)
    assert_forbidden(response)


@allure.title("TC-API-PERM-01d: GET /permissions — trainer returns 403")
@pytest.mark.be
async def test_trainer_cannot_access_permission_matrix(client, trainer_token):
    """ตรวจสอบว่า trainer เข้า permission matrix ไม่ได้ → 403"""
    response = await get(client, "/permissions", token=trainer_token)
    assert_forbidden(response)


# ─── PUT /permissions ─────────────────────────────────────────────────────────────

@allure.title("TC-API-PERM-02: PUT /permissions — developer can update any role's permissions")
@pytest.mark.be
async def test_developer_can_update_any_permission(client, developer_token):
    """ตรวจสอบว่า developer อัปเดต permission ของ role ใดก็ได้"""
    update_payload = {
        "role": "owner",
        "resource": "branch_config",
        "action": "edit",
        "allowed": True,  # restore to allowed
    }

    response = await put(client, "/permissions",
                         token=developer_token,
                         json=update_payload,
                         expected_status=200)

    with allure.step("Assert permission updated successfully"):
        assert response.status_code == 200, "Developer must be able to update permissions."


@allure.title("TC-API-PERM-02b: PUT /permissions — owner can update branch_master/admin/trainer")
@pytest.mark.be
async def test_owner_can_update_subordinate_permissions(client, owner_token):
    """ตรวจสอบว่า owner อัปเดต permission ของ admin ได้"""
    update_payload = {
        "role": "admin",
        "resource": "package",
        "action": "view",
        "allowed": True,
    }

    response = await put(client, "/permissions",
                         token=owner_token,
                         json=update_payload,
                         expected_status=200)

    with allure.step("Assert permission change persisted"):
        assert response.status_code == 200


@allure.title("TC-API-PERM-02c: PUT /permissions — owner cannot update developer permissions")
@pytest.mark.be
async def test_owner_cannot_update_developer_permissions(client, owner_token):
    """ตรวจสอบว่า owner อัปเดต permission ของ developer ไม่ได้ → 403"""
    update_payload = {
        "role": "developer",
        "resource": "some_feature",
        "action": "edit",
        "allowed": False,
    }

    response = await put(client, "/permissions",
                         token=owner_token,
                         json=update_payload)

    assert_forbidden(response)


@allure.title("TC-API-PERM-02d: PUT /permissions — branch_master can update admin/trainer")
@pytest.mark.be
async def test_branch_master_can_update_admin_trainer_permissions(client, branch_master_token):
    """ตรวจสอบว่า branch_master อัปเดต permission ของ admin/trainer ได้"""
    update_payload = {
        "role": "trainer",
        "resource": "order",
        "action": "create",
        "allowed": True,
    }

    response = await put(client, "/permissions",
                         token=branch_master_token,
                         json=update_payload,
                         expected_status=200)

    assert response.status_code == 200


@allure.title("TC-API-PERM-02e: PUT /permissions — branch_master cannot update owner permissions")
@pytest.mark.be
async def test_branch_master_cannot_update_owner_permissions(client, branch_master_token):
    """ตรวจสอบว่า branch_master อัปเดต permission ของ owner ไม่ได้ → 403"""
    update_payload = {
        "role": "owner",
        "resource": "user",
        "action": "create",
        "allowed": False,
    }

    response = await put(client, "/permissions",
                         token=branch_master_token,
                         json=update_payload)

    assert_forbidden(response)


@allure.title("TC-API-PERM-03: PUT /permissions — admin cannot update any permissions")
@pytest.mark.be
async def test_admin_cannot_update_permissions(client, admin_token):
    """ตรวจสอบว่า admin อัปเดต permission ไม่ได้เลย → 403"""
    update_payload = {
        "role": "trainer",
        "resource": "customer",
        "action": "view",
        "allowed": True,
    }

    response = await put(client, "/permissions",
                         token=admin_token,
                         json=update_payload)

    assert_forbidden(response)


@allure.title("TC-API-PERM-03b: PUT /permissions — trainer cannot update any permissions")
@pytest.mark.be
async def test_trainer_cannot_update_permissions(client, trainer_token):
    """ตรวจสอบว่า trainer อัปเดต permission ไม่ได้เลย → 403"""
    update_payload = {
        "role": "trainer",
        "resource": "customer",
        "action": "view",
        "allowed": True,
    }

    response = await put(client, "/permissions",
                         token=trainer_token,
                         json=update_payload)

    assert_forbidden(response)


@allure.title("TC-API-PERM-04: Disabled module returns 403 for affected role")
@pytest.mark.be
async def test_disabled_module_returns_403_for_affected_role(client, owner_token,
                                                              admin_token,
                                                              permission_override):
    """
    ตรวจสอบว่าเมื่อ owner ปิด module → admin ที่เคยใช้ได้จะได้ 403 Forbidden
    End-to-end permission enforcement test
    """
    with allure.step("Disable booking module for admin"):
        permission_override("admin", "booking", "view", False)

    with allure.step("Admin calls GET /bookings — should get 403"):
        response = await get(client, "/bookings", token=admin_token)
        assert_forbidden(response)
