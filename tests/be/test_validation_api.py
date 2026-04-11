# tests/be/test_validation_api.py
#
# BE tests สำหรับ Input Validation
# TC-API-VAL-01 ถึง TC-API-VAL-04

import pytest
import allure
from helpers.common_api import (
    post,
    assert_validation_error,
    build_customer_payload, build_order_payload,
)


@allure.title("TC-API-VAL-01: Future birthdate rejected")
@pytest.mark.be
async def test_future_birthdate_rejected(client, admin_token, seed_data):
    """ตรวจสอบว่า birthdate ที่เป็นวันในอนาคต → 422 Unprocessable Entity"""
    pattaya_branch = seed_data["branches"][0]
    mkt_source_type = seed_data["source_types"]["BPY_MKT"]

    customer_payload = build_customer_payload(
        branch_id=str(pattaya_branch.id),
        source_type_id=str(mkt_source_type.id),
        birthday="2099-01-01",  # วันในอนาคต
    )

    response = await post(client, "/customers",
                          token=admin_token,
                          json=customer_payload)

    with allure.step("Assert 422 — future birthdate rejected"):
        assert_validation_error(response)


@allure.title("TC-API-VAL-02a: Invalid email format rejected on POST /customers")
@pytest.mark.be
async def test_invalid_email_format_rejected_on_customer(client, admin_token, seed_data):
    """ตรวจสอบว่า email format ไม่ถูก → 422 ใน POST /customers"""
    pattaya_branch = seed_data["branches"][0]
    mkt_source_type = seed_data["source_types"]["BPY_MKT"]

    customer_payload = build_customer_payload(
        branch_id=str(pattaya_branch.id),
        source_type_id=str(mkt_source_type.id),
        email="not-an-email",
    )

    response = await post(client, "/customers",
                          token=admin_token,
                          json=customer_payload)

    assert_validation_error(response)


@allure.title("TC-API-VAL-02b: Invalid email format rejected on POST /trainers")
@pytest.mark.be
async def test_invalid_email_format_rejected_on_trainer(client, admin_token, seed_data):
    """ตรวจสอบว่า email format ไม่ถูก → 422 ใน POST /trainers"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    response = await post(client, "/trainers",
                          token=admin_token,
                          json={
                              "name": "Invalid Email Trainer",
                              "email": "bad-email",
                              "branch_id": pattaya_branch_id,
                              "status": "ACTIVE",
                          })

    assert_validation_error(response)


@allure.title("TC-API-VAL-02c: Invalid email format rejected on POST /caretakers")
@pytest.mark.be
async def test_invalid_email_format_rejected_on_caretaker(client, admin_token, seed_data):
    """ตรวจสอบว่า email format ไม่ถูก → 422 ใน POST /caretakers"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    response = await post(client, "/caretakers",
                          token=admin_token,
                          json={
                              "name": "Invalid Email Caretaker",
                              "email": "not-valid",
                              "branch_id": pattaya_branch_id,
                              "status": "ACTIVE",
                          })

    assert_validation_error(response)


@allure.title("TC-API-VAL-03: Negative hours rejected in order")
@pytest.mark.be
async def test_negative_hours_rejected_in_order(client, admin_token,
                                                 create_customer, create_package, seed_data):
    """ตรวจสอบว่า hours ติดลบ → 422 Unprocessable Entity"""
    customer_id = create_customer(branch="pattaya")
    package_id = create_package()
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
        hours=-1,
        bonus_hours=-2,
    )

    response = await post(client, "/orders", token=admin_token, json=order_payload)
    assert_validation_error(response)


@allure.title("TC-API-VAL-04: Negative total_price rejected in order")
@pytest.mark.be
async def test_negative_price_rejected_in_order(client, admin_token,
                                                 create_customer, create_package, seed_data):
    """ตรวจสอบว่า total_price ติดลบ → 422 Unprocessable Entity"""
    customer_id = create_customer(branch="pattaya")
    package_id = create_package()
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
        total_price=-500.0,
    )

    response = await post(client, "/orders", token=admin_token, json=order_payload)
    assert_validation_error(response)
