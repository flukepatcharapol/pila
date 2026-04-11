# tests/be/test_user_api.py
#
# BE tests สำหรับ User Management API
# TC-API-USER-01 ถึง TC-API-USER-08

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_forbidden, assert_branch_scope,
)


# ─── GET /users ───────────────────────────────────────────────────────────────────

@allure.title("TC-API-USER-01: GET /users — developer sees all users across all partners")
@pytest.mark.be
async def test_developer_sees_all_users(client, developer_token, seed_data):
    """ตรวจสอบว่า developer เห็น user ทุก partner ทุก branch"""
    response = await get(client, "/users", token=developer_token, expected_status=200)

    with allure.step("Assert users from multiple roles and branches present"):
        user_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        role_set = {user_record["role"] for user_record in user_list}
        assert len(role_set) >= 2, (
            f"Developer should see users from multiple roles "
            f"but only saw roles: {role_set}."
        )


@allure.title("TC-API-USER-01b: GET /users — owner sees all users within partner")
@pytest.mark.be
async def test_owner_sees_partner_users_only(client, owner_token, seed_data):
    """ตรวจสอบว่า owner เห็น user ทุก branch ใน partner ตัวเอง"""
    partner_id = str(seed_data["partner"].id)

    response = await get(client, "/users", token=owner_token, expected_status=200)

    with allure.step("Assert all returned users belong to owner's partner"):
        user_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        for user_record in user_list:
            assert user_record.get("partner_id") == partner_id, (
                f"User {user_record.get('id')} belongs to partner {user_record.get('partner_id')} "
                f"but owner should only see users from partner {partner_id}."
            )


@allure.title("TC-API-USER-01c: GET /users — branch_master sees only own branch users")
@pytest.mark.be
async def test_branch_master_sees_own_branch_users_only(client, branch_master_token,
                                                         seed_data):
    """ตรวจสอบว่า branch_master เห็นเฉพาะ user ในสาขาที่ assigned"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    response = await get(client, "/users", token=branch_master_token, expected_status=200)

    with allure.step("Assert all returned users belong to Pattaya branch"):
        user_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        for user_record in user_list:
            user_branch_id = user_record.get("branch_id")
            if user_branch_id:  # owner/developer may have no branch_id
                assert user_branch_id == pattaya_branch_id, (
                    f"User {user_record.get('id')} is in branch {user_branch_id} "
                    f"but branch_master should only see Pattaya users."
                )


# ─── POST /users ──────────────────────────────────────────────────────────────────

@allure.title("TC-API-USER-02: POST /users — owner creates branch_master in own partner")
@pytest.mark.be
async def test_owner_creates_branch_master(client, owner_token, seed_data):
    """ตรวจสอบว่า owner สร้าง BRANCH_MASTER ใน partner ตัวเองได้ → 201 Created"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    new_user_payload = {
        "username": "new_bm",
        "email": "new_bm@test.com",
        "password": "secure_password",
        "role": "BRANCH_MASTER",
        "branch_id": pattaya_branch_id,
    }

    response = await post(client, "/users",
                          token=owner_token,
                          json=new_user_payload,
                          expected_status=201)

    with allure.step("Assert BRANCH_MASTER created"):
        created_user = response.json()
        assert created_user.get("role") == "BRANCH_MASTER", (
            f"Expected role='BRANCH_MASTER' but got '{created_user.get('role')}'."
        )


@allure.title("TC-API-USER-02b: POST /users — branch_master creates admin in own branch")
@pytest.mark.be
async def test_branch_master_creates_admin(client, branch_master_token, seed_data):
    """ตรวจสอบว่า branch_master สร้าง ADMIN ในสาขาตัวเองได้ → 201 Created"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    new_admin_payload = {
        "username": "new_admin_bm",
        "email": "new_admin_bm@test.com",
        "password": "secure_password",
        "role": "ADMIN",
        "branch_id": pattaya_branch_id,
    }

    response = await post(client, "/users",
                          token=branch_master_token,
                          json=new_admin_payload,
                          expected_status=201)

    with allure.step("Assert ADMIN created in Pattaya"):
        created_user = response.json()
        assert created_user.get("role") == "ADMIN"
        assert created_user.get("branch_id") == pattaya_branch_id


@allure.title("TC-API-USER-02c: POST /users — branch_master creates trainer in own branch")
@pytest.mark.be
async def test_branch_master_creates_trainer(client, branch_master_token, seed_data):
    """ตรวจสอบว่า branch_master สร้าง TRAINER ในสาขาตัวเองได้ → 201 Created"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    new_trainer_payload = {
        "username": "new_trainer_bm",
        "email": "new_trainer_bm@test.com",
        "password": "secure_password",
        "role": "TRAINER",
        "branch_id": pattaya_branch_id,
    }

    await post(client, "/users",
               token=branch_master_token,
               json=new_trainer_payload,
               expected_status=201)


@allure.title("TC-API-USER-03: POST /users — branch_master cannot create user in other branch")
@pytest.mark.be
async def test_branch_master_cannot_create_user_in_other_branch(client, branch_master_token,
                                                                  seed_data):
    """ตรวจสอบว่า branch_master สร้าง user ในสาขาอื่น → 403 Forbidden"""
    kanchanaburi_branch_id = str(seed_data["kanchanaburi"].id)

    cross_branch_payload = {
        "username": "cross_branch_user",
        "email": "cross@test.com",
        "password": "secure_password",
        "role": "ADMIN",
        "branch_id": kanchanaburi_branch_id,
    }

    response = await post(client, "/users",
                          token=branch_master_token,
                          json=cross_branch_payload)

    assert_forbidden(response)


@allure.title("TC-API-USER-03b: POST /users — branch_master cannot create owner or branch_master")
@pytest.mark.be
async def test_branch_master_cannot_create_equal_or_higher_role(client, branch_master_token,
                                                                  seed_data):
    """
    ตรวจสอบว่า branch_master ไม่สามารถสร้าง OWNER หรือ BRANCH_MASTER → 403 Forbidden
    ไม่สามารถสร้าง role ที่เท่ากันหรือสูงกว่า
    """
    pattaya_branch_id = str(seed_data["pattaya"].id)

    elevated_role_payload = {
        "username": "elevated_user",
        "email": "elevated@test.com",
        "password": "secure_password",
        "role": "OWNER",
        "branch_id": pattaya_branch_id,
    }

    response = await post(client, "/users",
                          token=branch_master_token,
                          json=elevated_role_payload)

    assert_forbidden(response)


@allure.title("TC-API-USER-03c: POST /users — admin cannot create any user")
@pytest.mark.be
async def test_admin_cannot_create_user(client, admin_token, seed_data):
    """ตรวจสอบว่า admin สร้าง user ไม่ได้เลย → 403 Forbidden"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    response = await post(client, "/users",
                          token=admin_token,
                          json={
                              "username": "blocked_user",
                              "email": "blocked@test.com",
                              "password": "secure_password",
                              "role": "TRAINER",
                              "branch_id": pattaya_branch_id,
                          })

    assert_forbidden(response)


@allure.title("TC-API-USER-04: POST /users — password stored as bcrypt hash")
@pytest.mark.be
async def test_user_password_stored_as_hash(client, owner_token, seed_data, db_session):
    """ตรวจสอบว่า password ถูก hash ก่อน store ใน DB — ไม่เป็น plaintext"""
    from api.models import User

    pattaya_branch_id = str(seed_data["pattaya"].id)
    plaintext_password = "plaintext_password_for_test"

    response = await post(client, "/users",
                          token=owner_token,
                          json={
                              "username": "hash_test_user",
                              "email": "hashtest@test.com",
                              "password": plaintext_password,
                              "role": "ADMIN",
                              "branch_id": pattaya_branch_id,
                          },
                          expected_status=201)

    with allure.step("Query DB and verify password is not plaintext"):
        created_user_id = response.json().get("id")
        stored_user = db_session.query(User).filter_by(id=created_user_id).first()
        assert stored_user is not None, "Created user must exist in DB."
        assert stored_user.password_hash != plaintext_password, (
            "Password must NOT be stored as plaintext. "
            "Bcrypt hashing is required for all passwords."
        )
        assert stored_user.password_hash.startswith("$2"), (
            f"Password hash '{stored_user.password_hash[:10]}...' does not look like bcrypt. "
            "Expected bcrypt hash starting with '$2'."
        )


# ─── PUT /users/:id/role ──────────────────────────────────────────────────────────

@allure.title("TC-API-USER-05: PUT /users/:id/role — only owner/developer can change roles")
@pytest.mark.be
async def test_admin_cannot_change_user_role(client, admin_token,
                                              create_user, seed_data):
    """ตรวจสอบว่า admin เปลี่ยน role ไม่ได้ → 403 Forbidden"""
    target_user_id = create_user(role="TRAINER", branch="pattaya")

    response = await put(client, f"/users/{target_user_id}/role",
                         token=admin_token,
                         json={"role": "ADMIN"})

    assert_forbidden(response)


@allure.title("TC-API-USER-05b: PUT /users/:id/role — branch_master cannot elevate to owner")
@pytest.mark.be
async def test_branch_master_cannot_elevate_to_owner(client, branch_master_token,
                                                      create_user):
    """ตรวจสอบว่า branch_master เปลี่ยน role ไปเป็น OWNER ไม่ได้ → 403 Forbidden"""
    target_user_id = create_user(role="ADMIN", branch="pattaya")

    response = await put(client, f"/users/{target_user_id}/role",
                         token=branch_master_token,
                         json={"role": "OWNER"})

    assert_forbidden(response)


# ─── DELETE /users/:id ────────────────────────────────────────────────────────────

@allure.title("TC-API-USER-06: DELETE /users/:id — owner can deactivate user")
@pytest.mark.be
async def test_owner_can_deactivate_user(client, owner_token, create_user):
    """ตรวจสอบว่า owner deactivate user ได้ → 200 OK, status=inactive"""
    target_user_id = create_user(role="ADMIN", branch="pattaya")

    response = await delete(client, f"/users/{target_user_id}",
                            token=owner_token, expected_status=200)

    with allure.step("Assert user status set to inactive"):
        user_data = response.json()
        is_active = user_data.get("is_active", True)
        assert is_active is False, (
            f"Expected is_active=False after deactivation but got {is_active}."
        )


@allure.title("TC-API-USER-07: DELETE /users/:id — cannot deactivate own account")
@pytest.mark.be
async def test_cannot_deactivate_own_account(client, owner_token, seed_data):
    """ตรวจสอบว่า owner ลบตัวเองไม่ได้ → 400 Bad Request"""
    owner_user_id = str(seed_data["users"]["owner"].id)

    response = await delete(client, f"/users/{owner_user_id}",
                            token=owner_token)

    with allure.step("Assert 400 — cannot deactivate own account"):
        assert response.status_code == 400, (
            f"Expected 400 when deactivating own account but got {response.status_code}. "
            "Users must not be able to deactivate themselves."
        )


@allure.title("TC-API-USER-08: DELETE /users/:id — cannot deactivate user with higher role")
@pytest.mark.be
async def test_cannot_deactivate_higher_role_user(client, branch_master_token, seed_data):
    """ตรวจสอบว่า branch_master ลบ owner ไม่ได้ → 403 Forbidden"""
    owner_user_id = str(seed_data["users"]["owner"].id)

    response = await delete(client, f"/users/{owner_user_id}",
                            token=branch_master_token)

    assert_forbidden(response)
