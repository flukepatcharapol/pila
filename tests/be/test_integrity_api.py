# tests/be/test_integrity_api.py
#
# BE tests สำหรับ Data Integrity
# TC-API-INT-01 ถึง TC-API-INT-05

import pytest
import allure
from helpers.common_api import (
    delete, post,
    assert_conflict,
)


@allure.title("TC-API-INT-01: DELETE /branches/:id — fail if branch has customers")
@pytest.mark.be
async def test_delete_branch_with_customers_rejected(client, owner_token,
                                                      create_customer, seed_data):
    """ตรวจสอบว่าลบ branch ที่มี customer อยู่ → 409 Conflict"""
    create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)

    response = await delete(client, f"/branches/{pattaya_branch_id}",
                            token=owner_token)

    assert_conflict(response, expected_detail="existing customers")


@allure.title("TC-API-INT-02: DELETE /trainers/:id — fail if trainer has active booking")
@pytest.mark.be
async def test_delete_trainer_with_active_booking_rejected_integrity(client, admin_token,
                                                                       create_trainer,
                                                                       confirmed_booking,
                                                                       db_session):
    """
    ตรวจสอบว่าลบ trainer ที่มี confirmed booking → 409 Conflict
    Data integrity: ไม่ orphaned bookings
    """
    from api.models import Booking

    trainer_id = create_trainer(branch="pattaya")
    booking_record = db_session.query(Booking).filter_by(id=confirmed_booking).first()
    if booking_record:
        booking_record.trainer_id = trainer_id
        db_session.flush()

    response = await delete(client, f"/trainers/{trainer_id}",
                            token=admin_token)

    assert_conflict(response, expected_detail="active bookings")


@allure.title("TC-API-INT-03: DELETE /packages/:id — fail if package used in order")
@pytest.mark.be
async def test_delete_package_referenced_by_order_rejected(client, owner_token,
                                                            create_package, create_order):
    """ตรวจสอบว่าลบ package ที่มี order อ้างอิง → 409 Conflict"""
    package_id = create_package()
    create_order(package_id=package_id)

    response = await delete(client, f"/packages/{package_id}",
                            token=owner_token)

    assert_conflict(response, expected_detail="existing orders")


@allure.title("TC-API-INT-04: Session balance never goes negative — DB constraint enforced")
@pytest.mark.be
@pytest.mark.slow
async def test_session_balance_never_negative_db_constraint(client, admin_token,
                                                              customer_with_balance,
                                                              seed_data, db_session):
    """
    ตรวจสอบว่า DB constraint ป้องกัน balance ติดลบ
    แม้ 2 concurrent deductions บน balance=1 → final balance ต้องเป็น 0
    """
    import asyncio

    customer_id = customer_with_balance(hours=1)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    deduction_payload = {
        "customer_id": customer_id,
        "branch_id": pattaya_branch_id,
    }

    with allure.step("Send 2 concurrent deductions on balance=1"):
        await asyncio.gather(
            post(client, "/customer-hours/deduct",
                 token=admin_token, json=deduction_payload),
            post(client, "/customer-hours/deduct",
                 token=admin_token, json=deduction_payload),
            return_exceptions=True,
        )

    with allure.step("Query DB — assert balance is 0 (not -1)"):
        from api.models import CustomerHourBalance
        db_session.expire_all()
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        assert hour_balance_record.remaining >= 0, (
            f"Hour balance is {hour_balance_record.remaining} which is negative. "
            "DB constraint must prevent session balance from going below 0."
        )
        assert hour_balance_record.remaining == 0, (
            f"Expected balance=0 after 2 concurrent deductions on balance=1 "
            f"but got {hour_balance_record.remaining}."
        )


@allure.title("TC-API-INT-05: Customer code unique at DB level — concurrent creation")
@pytest.mark.be
@pytest.mark.slow
async def test_customer_code_unique_at_db_level(client, admin_token, seed_data):
    """
    ตรวจสอบว่า customer code unique constraint ใน DB ป้องกัน duplicate
    แม้ 2 concurrent requests สร้างพร้อมกัน
    """
    import asyncio

    pattaya_branch = seed_data["branches"][0]
    mkt_source_type = seed_data["source_types"]["BPY_MKT"]

    customer_payload = {
        "branch_id": str(pattaya_branch.id),
        "source_type_id": str(mkt_source_type.id),
        "first_name": "Unique Code Test",
        "last_name": "Customer",
        "phone": "0812345678",
        "status": "ACTIVE",
    }

    with allure.step("Send 2 concurrent POST /customers requests"):
        response_list = await asyncio.gather(
            post(client, "/customers", token=admin_token, json=customer_payload),
            post(client, "/customers", token=admin_token, json=customer_payload),
            return_exceptions=True,
        )

    with allure.step("Assert no duplicate customer codes in DB"):
        success_responses = [
            res for res in response_list
            if not isinstance(res, Exception) and res.status_code == 201
        ]
        customer_codes = [res.json().get("customer_code") for res in success_responses]
        code_set = set(customer_codes)
        assert len(customer_codes) == len(code_set), (
            f"Duplicate customer codes detected: {customer_codes}. "
            "DB unique constraint must prevent duplicate codes."
        )
