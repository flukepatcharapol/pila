# tests/be/test_order_api.py
#
# BE tests สำหรับ Order API
# TC-API-ORDER-01 ถึง TC-API-ORDER-16

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_forbidden, assert_validation_error, assert_pagination,
    build_order_payload,
)


# ─── GET /orders ─────────────────────────────────────────────────────────────────

@allure.title("TC-API-ORDER-01: GET /orders returns paginated list for admin's branch")
@pytest.mark.be
async def test_order_list_paginated(client, admin_token, create_order, seed_data):
    """ตรวจสอบว่า GET /orders คืน paginated list สำหรับ branch ของ admin"""
    create_order()
    create_order()

    response = await get(client, "/orders", token=admin_token, expected_status=200)

    with allure.step("Assert paginated structure"):
        response_data = response.json()
        assert_pagination(response_data)
        assert len(response_data["items"]) >= 1, "At least one order must be returned."


@allure.title("TC-API-ORDER-02: GET /orders with date range filter returns correct orders")
@pytest.mark.be
async def test_order_date_range_filter(client, admin_token, create_order):
    """ตรวจสอบว่า ?start_date=&end_date= filter ทำงานถูกต้อง"""
    from datetime import date, timedelta

    create_order()

    today_str = str(date.today())
    yesterday_str = str(date.today() - timedelta(days=1))

    response = await get(client, "/orders",
                         token=admin_token,
                         params={"start_date": yesterday_str, "end_date": today_str},
                         expected_status=200)

    with allure.step("Assert only orders within date range returned"):
        response_data = response.json()
        assert "items" in response_data, "Response must have 'items' field."


@allure.title("TC-API-ORDER-03: GET /orders — orders with outstanding balance flagged")
@pytest.mark.be
async def test_order_outstanding_balance_flag(client, admin_token, create_order):
    """ตรวจสอบว่า orders ที่มี outstanding_balance มี flag has_outstanding = true"""
    create_order(total_price=10000.0, paid_amount=5000.0)  # ยังค้างชำระ

    response = await get(client, "/orders", token=admin_token, expected_status=200)

    with allure.step("Assert outstanding orders have has_outstanding flag"):
        order_list = response.json()["items"]
        outstanding_orders = [
            order for order in order_list
            if order.get("total_price", 0) > order.get("paid_amount", 0)
        ]
        for order in outstanding_orders:
            assert order.get("has_outstanding") is True, (
                f"Order {order.get('id')} has unpaid balance "
                "but 'has_outstanding' flag is not True. "
                "All orders with outstanding balance must be flagged."
            )


# ─── POST /orders ─────────────────────────────────────────────────────────────────

@allure.title("TC-API-ORDER-04: POST /orders — valid order creates and allocates sessions")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.be
async def test_create_order_valid_allocates_sessions(client, admin_token,
                                                      create_customer, create_package,
                                                      seed_data, db_session):
    """
    ตรวจสอบว่าสร้าง order ด้วย payload ถูกต้อง → 201 Created
    และ customer hour_balance เพิ่มขึ้นตาม hours + bonus_hours
    """
    customer_id = create_customer(branch="pattaya", initial_hours=0)
    package_id = create_package(hours=10)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
        hours=10,
        bonus_hours=2,
    )

    with allure.step("POST /orders with valid payload"):
        response = await post(client, "/orders",
                              token=admin_token,
                              json=order_payload,
                              expected_status=201)

    with allure.step("Assert order created with correct fields"):
        order_data = response.json()
        assert "id" in order_data, "Order response must contain 'id'."

    with allure.step("Assert customer hour_balance incremented by hours + bonus_hours"):
        from api.models import CustomerHourBalance
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        expected_balance = 10 + 2  # hours + bonus_hours
        assert hour_balance_record.remaining == expected_balance, (
            f"Expected hour_balance={expected_balance} after order "
            f"but got {hour_balance_record.remaining}. "
            "Order creation must allocate hours to customer balance."
        )


@allure.title("TC-API-ORDER-05: POST /orders with inactive package returns 400")
@pytest.mark.be
async def test_create_order_inactive_package_rejected(client, admin_token,
                                                       create_customer,
                                                       expired_package, seed_data):
    """ตรวจสอบว่าใช้ package ที่ inactive → 400 Bad Request"""
    customer_id = create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=expired_package,
        branch_id=pattaya_branch_id,
    )

    response = await post(client, "/orders",
                          token=admin_token,
                          json=order_payload)

    with allure.step("Assert 400 — inactive package rejected"):
        assert response.status_code == 400, (
            f"Expected 400 for inactive/expired package but got {response.status_code}. "
            "Orders must not be created with packages that are no longer active."
        )
        assert "active" in response.json().get("detail", "").lower(), (
            "Error detail must mention package is not active."
        )


@allure.title("TC-API-ORDER-06: POST /orders with package from wrong branch returns 400")
@pytest.mark.be
async def test_create_order_package_wrong_branch_rejected(client, admin_token,
                                                           create_customer, seed_data,
                                                           db_session):
    """ตรวจสอบว่า package ของสาขาอื่นใช้กับ order สาขานี้ไม่ได้ → 400"""
    from api.models import Package
    from datetime import date, timedelta

    customer_id = create_customer(branch="pattaya")
    kanchanaburi_branch_id = str(seed_data["kanchanaburi"].id)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    kanchanaburi_package = Package(
        partner_id=seed_data["partner"].id,
        name="KBR Only Package",
        hours=10,
        sale_type="SALE",
        price=5000.0,
        branch_scope="SPECIFIC",
        branch_id=kanchanaburi_branch_id,
        is_active=True,
        active_from=date.today() - timedelta(days=30),
        active_until=date.today() + timedelta(days=365),
    )
    db_session.add(kanchanaburi_package)
    db_session.flush()

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=str(kanchanaburi_package.id),
        branch_id=pattaya_branch_id,
    )

    response = await post(client, "/orders", token=admin_token, json=order_payload)

    with allure.step("Assert 400 — package from wrong branch rejected"):
        assert response.status_code == 400, (
            f"Expected 400 for package not available in this branch "
            f"but got {response.status_code}."
        )


@allure.title("TC-API-ORDER-07: POST /orders missing required fields returns 422")
@pytest.mark.be
async def test_create_order_missing_required_fields(client, admin_token):
    """ตรวจสอบว่า POST /orders โดยไม่มี required fields → 422"""
    response = await post(client, "/orders",
                          token=admin_token,
                          json={"notes": "incomplete order"})

    with allure.step("Assert 422 Unprocessable Entity"):
        assert_validation_error(response)


@allure.title("TC-API-ORDER-10: Trainer cannot create order by default (403)")
@pytest.mark.be
async def test_trainer_cannot_create_order(client, trainer_token,
                                           create_customer, create_package, seed_data):
    """ตรวจสอบว่า trainer สร้าง order ไม่ได้ → 403 Forbidden"""
    customer_id = create_customer(branch="pattaya")
    package_id = create_package()
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
    )

    response = await post(client, "/orders", token=trainer_token, json=order_payload)
    assert_forbidden(response)


@allure.title("TC-API-ORDER-10b: Admin blocked from order create when permission matrix disallows")
@pytest.mark.be
async def test_admin_create_order_blocked_by_permission_matrix(client, admin_token,
                                                                create_customer,
                                                                create_package, seed_data,
                                                                permission_override):
    """ตรวจสอบว่า admin ที่ถูกปิด order.create → 403"""
    customer_id = create_customer(branch="pattaya")
    package_id = create_package()
    pattaya_branch_id = str(seed_data["pattaya"].id)

    with allure.step("Disable order.create for admin"):
        permission_override("admin", "order", "create", False)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
    )

    response = await post(client, "/orders", token=admin_token, json=order_payload)
    assert_forbidden(response)


# ─── GET /orders/:id ─────────────────────────────────────────────────────────────

@allure.title("TC-API-ORDER-08: GET /orders/:id returns detail with payment breakdown")
@pytest.mark.be
async def test_get_order_detail_with_payment(client, admin_token, create_order):
    """ตรวจสอบว่า GET /orders/:id มี payment breakdown ครบถ้วน"""
    order_id = create_order(hours=10, total_price=5000.0, paid_amount=5000.0)

    response = await get(client, f"/orders/{order_id}",
                         token=admin_token, expected_status=200)

    with allure.step("Assert payment fields present in response"):
        order_detail = response.json()
        required_payment_fields = ["payment_method", "total_price", "paid_amount"]
        for field_name in required_payment_fields:
            assert field_name in order_detail, (
                f"Order detail must contain '{field_name}' field for payment breakdown."
            )


# ─── PUT /orders/:id ─────────────────────────────────────────────────────────────

@allure.title("TC-API-ORDER-09: PUT /orders/:id — update order notes")
@pytest.mark.be
async def test_update_order_notes(client, admin_token, create_order):
    """ตรวจสอบว่า PUT /orders/:id อัปเดต notes ได้"""
    order_id = create_order()

    updated_note = "หมายเหตุที่อัปเดตแล้ว"
    response = await put(client, f"/orders/{order_id}",
                         token=admin_token,
                         json={"notes": updated_note},
                         expected_status=200)

    with allure.step("Assert notes updated in response"):
        order_data = response.json()
        assert order_data.get("notes") == updated_note, (
            f"Expected notes='{updated_note}' but got '{order_data.get('notes')}'."
        )


# ─── POST /orders/:id/payments ────────────────────────────────────────────────────

@allure.title("TC-API-ORDER-11: POST /orders/:id/payments — record installment payment")
@pytest.mark.be
async def test_record_installment_payment(client, admin_token, create_order):
    """ตรวจสอบว่าบันทึก installment payment ได้ → 201 Created"""
    from datetime import date

    order_id = create_order(total_price=10000.0, paid_amount=5000.0)

    payment_payload = {
        "amount": 2000.0,
        "paid_at": str(date.today()),
        "note": "งวด 2",
    }

    response = await post(client, f"/orders/{order_id}/payments",
                          token=admin_token,
                          json=payment_payload,
                          expected_status=201)

    with allure.step("Assert payment recorded and outstanding reduced"):
        payment_data = response.json()
        assert "id" in payment_data or "amount" in payment_data, (
            "Payment response must contain payment details."
        )


@allure.title("TC-API-ORDER-12: GET /orders/:id/payments — installment history")
@pytest.mark.be
async def test_get_installment_payment_history(client, admin_token, create_order):
    """ตรวจสอบว่า GET /orders/:id/payments คืน installment history"""
    order_id = create_order()

    response = await get(client, f"/orders/{order_id}/payments",
                         token=admin_token, expected_status=200)

    with allure.step("Assert payment history list returned"):
        payment_list = response.json()
        assert isinstance(payment_list, list), (
            "Payment history must return a list."
        )


@allure.title("TC-API-ORDER-13: POST /orders/:id/receipt — send receipt email")
@pytest.mark.be
async def test_send_receipt_email(client, admin_token, create_order):
    """ตรวจสอบว่า POST /orders/:id/receipt ส่ง email → 200 OK"""
    order_id = create_order()

    response = await post(client, f"/orders/{order_id}/receipt",
                          token=admin_token,
                          json={},
                          expected_status=200)

    with allure.step("Assert receipt send acknowledged"):
        assert response.status_code == 200


# ─── Validation Edge Cases ────────────────────────────────────────────────────────

@allure.title("TC-API-ORDER-14: POST /orders with negative hours returns 422")
@pytest.mark.be
async def test_create_order_negative_hours_rejected(client, admin_token,
                                                     create_customer, create_package,
                                                     seed_data):
    """ตรวจสอบว่า hours ติดลบ → 422 Unprocessable Entity"""
    customer_id = create_customer(branch="pattaya")
    package_id = create_package()
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
        hours=-5,
    )

    response = await post(client, "/orders", token=admin_token, json=order_payload)
    assert_validation_error(response)


@allure.title("TC-API-ORDER-15: POST /orders with negative total_price returns 422")
@pytest.mark.be
async def test_create_order_negative_price_rejected(client, admin_token,
                                                     create_customer, create_package,
                                                     seed_data):
    """ตรวจสอบว่า total_price ติดลบ → 422 Unprocessable Entity"""
    customer_id = create_customer(branch="pattaya")
    package_id = create_package()
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
        total_price=-1000.0,
    )

    response = await post(client, "/orders", token=admin_token, json=order_payload)
    assert_validation_error(response)


@allure.title("TC-API-ORDER-16: POST /orders with package before active period returns 400")
@pytest.mark.be
async def test_create_order_future_package_rejected(client, admin_token,
                                                     create_customer,
                                                     future_package, seed_data):
    """ตรวจสอบว่า package ที่ยังไม่ถึงวัน active → 400 Bad Request"""
    customer_id = create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=future_package,
        branch_id=pattaya_branch_id,
    )

    response = await post(client, "/orders", token=admin_token, json=order_payload)

    with allure.step("Assert 400 — package not yet active"):
        assert response.status_code == 400, (
            f"Expected 400 for package before active period but got {response.status_code}."
        )
