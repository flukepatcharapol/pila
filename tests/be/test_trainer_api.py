# tests/be/test_trainer_api.py
#
# BE tests สำหรับ Trainer API
# TC-API-TRAINER-01 ถึง TC-API-TRAINER-06

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_forbidden, assert_conflict, assert_branch_scope,
)


# ─── GET /trainers ────────────────────────────────────────────────────────────────

@allure.title("TC-API-TRAINER-01: GET /trainers — admin sees only own branch trainers")
@pytest.mark.be
async def test_admin_sees_own_branch_trainers_only(client, admin_token,
                                                    create_trainer, seed_data):
    """ตรวจสอบว่า admin เห็นเฉพาะ trainer ของสาขาตัวเอง"""
    pattaya_branch_id = str(seed_data["pattaya"].id)
    create_trainer(branch="pattaya")
    create_trainer(branch="kanchanaburi")

    response = await get(client, "/trainers", token=admin_token, expected_status=200)

    with allure.step("Assert only Pattaya trainers returned"):
        trainer_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert_branch_scope(trainer_list, expected_branch_id=pattaya_branch_id)


@allure.title("TC-API-TRAINER-04: GET /trainers — owner sees all branches")
@pytest.mark.be
async def test_owner_sees_all_branch_trainers(client, owner_token,
                                               create_trainer, seed_data):
    """ตรวจสอบว่า owner เห็น trainer จากทุกสาขาใน partner"""
    create_trainer(branch="pattaya")
    create_trainer(branch="chachoengsao")
    create_trainer(branch="kanchanaburi")

    response = await get(client, "/trainers", token=owner_token, expected_status=200)

    with allure.step("Assert trainers from all branches present"):
        trainer_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        branch_id_set = {trainer["branch_id"] for trainer in trainer_list}
        assert len(branch_id_set) >= 2, (
            f"Owner should see trainers from multiple branches "
            f"but only saw {len(branch_id_set)} distinct branch(es)."
        )


# ─── POST /trainers ───────────────────────────────────────────────────────────────

@allure.title("TC-API-TRAINER-02: POST /trainers — create valid trainer")
@pytest.mark.be
async def test_create_trainer_valid(client, admin_token, seed_data):
    """ตรวจสอบว่าสร้าง trainer ด้วย payload ถูกต้อง → 201 Created"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    trainer_payload = {
        "name": "New Test Trainer",
        "email": "new_trainer@test.com",
        "branch_id": pattaya_branch_id,
        "status": "ACTIVE",
    }

    response = await post(client, "/trainers",
                          token=admin_token,
                          json=trainer_payload,
                          expected_status=201)

    with allure.step("Assert trainer created with correct branch"):
        trainer_data = response.json()
        assert trainer_data.get("branch_id") == pattaya_branch_id, (
            "Created trainer must belong to the specified branch."
        )
        assert trainer_data.get("status") == "ACTIVE", (
            "Created trainer must have ACTIVE status."
        )


# ─── PUT /trainers/:id ────────────────────────────────────────────────────────────

@allure.title("TC-API-TRAINER-05: PUT /trainers/:id — update trainer info")
@pytest.mark.be
async def test_update_trainer_info(client, admin_token, create_trainer):
    """ตรวจสอบว่าอัปเดต trainer info ได้ → 200 OK"""
    trainer_id = create_trainer(branch="pattaya")

    updated_email = "updated_trainer@test.com"
    response = await put(client, f"/trainers/{trainer_id}",
                         token=admin_token,
                         json={
                             "email": updated_email,
                             "status": "ACTIVE",
                         },
                         expected_status=200)

    with allure.step("Assert email updated in response"):
        trainer_data = response.json()
        assert trainer_data.get("email") == updated_email, (
            f"Expected email='{updated_email}' after update "
            f"but got '{trainer_data.get('email')}'."
        )


# ─── DELETE /trainers/:id ─────────────────────────────────────────────────────────

@allure.title("TC-API-TRAINER-03: DELETE /trainers/:id — fail if trainer has active customers")
@pytest.mark.be
async def test_delete_trainer_with_active_customers_rejected(client, admin_token,
                                                              create_trainer,
                                                              create_customer,
                                                              db_session, seed_data):
    """
    ตรวจสอบว่าลบ trainer ที่มี active customer assigned → 409 Conflict
    ป้องกัน orphaned customer records
    """
    from api.models import Customer

    trainer_id = create_trainer(branch="pattaya")
    customer_id = create_customer(branch="pattaya")

    with allure.step("Assign trainer to customer"):
        customer_record = db_session.query(Customer).filter_by(id=customer_id).first()
        customer_record.trainer_id = trainer_id
        db_session.flush()

    with allure.step("Attempt to delete trainer with active customers"):
        response = await delete(client, f"/trainers/{trainer_id}",
                                token=admin_token)

    with allure.step("Assert 409 Conflict"):
        assert_conflict(response, expected_detail="active customers")


@allure.title("TC-API-TRAINER-06: DELETE /trainers/:id — fail if trainer has active booking")
@pytest.mark.be
async def test_delete_trainer_with_active_booking_rejected(client, admin_token,
                                                            create_trainer,
                                                            create_booking):
    """
    ตรวจสอบว่าลบ trainer ที่มี confirmed booking → 409 Conflict
    """
    trainer_id = create_trainer(branch="pattaya")
    create_booking(status="confirmed", trainer_id=trainer_id)

    response = await delete(client, f"/trainers/{trainer_id}",
                            token=admin_token)

    assert_conflict(response, expected_detail="active bookings")
