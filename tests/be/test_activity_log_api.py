# tests/be/test_activity_log_api.py
#
# BE tests สำหรับ Activity Log API
# TC-API-LOG-01 ถึง TC-API-LOG-13

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_no_uuid_in_display_fields, assert_activity_log,
    build_customer_payload, build_order_payload,
)


# ─── GET /activity-log ────────────────────────────────────────────────────────────

@allure.title("TC-API-LOG-01: GET /activity-log — returns log entries with required fields")
@pytest.mark.be
async def test_activity_log_returns_entries(client, owner_token, create_customer):
    """ตรวจสอบว่า GET /activity-log คืน entries พร้อมครบ fields"""
    create_customer(branch="pattaya")  # trigger log creation

    response = await get(client, "/activity-log",
                         token=owner_token, expected_status=200)

    with allure.step("Assert required log fields present"):
        log_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert len(log_list) >= 1, "Activity log must have at least one entry."
        required_log_fields = ["timestamp", "action", "target_type", "target_id"]
        for log_entry in log_list:
            for field_name in required_log_fields:
                assert field_name in log_entry, (
                    f"Log entry must contain '{field_name}' field."
                )


@allure.title("TC-API-LOG-02: GET /activity-log with filters returns matching entries")
@pytest.mark.be
async def test_activity_log_filters_work(client, owner_token, seed_data):
    """ตรวจสอบว่า ?user_id=&action_type= filter ทำงานถูกต้อง"""
    admin_user_id = str(seed_data["users"]["admin"].id)

    response = await get(client, "/activity-log",
                         token=owner_token,
                         params={
                             "user_id": admin_user_id,
                             "action_type": "customer.create",
                         },
                         expected_status=200)

    with allure.step("Assert filtered log entries returned"):
        log_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert isinstance(log_list, list), "Filtered log must return a list."


# ─── Activity Log Auto-Creation ───────────────────────────────────────────────────

@allure.title("TC-API-LOG-03: Activity log created on customer.create")
@pytest.mark.be
async def test_activity_log_created_on_customer_create(client, admin_token,
                                                         seed_data, db_session):
    """ตรวจสอบว่าสร้าง customer → สร้าง activity log action='customer.create'"""
    pattaya_branch = seed_data["branches"][0]
    mkt_source_type = seed_data["source_types"]["BPY_MKT"]

    customer_payload = build_customer_payload(
        branch_id=str(pattaya_branch.id),
        source_type_id=str(mkt_source_type.id),
        first_name="Log Test",
        last_name="Customer",
    )

    response = await post(client, "/customers",
                          token=admin_token,
                          json=customer_payload,
                          expected_status=201)

    created_customer_id = response.json().get("id")

    with allure.step("Assert activity log created with action='customer.create'"):
        assert_activity_log(db_session, action="customer.create",
                            target_id=created_customer_id)


@allure.title("TC-API-LOG-04: Activity log created on customer_hour.deduct")
@pytest.mark.be
async def test_activity_log_created_on_hour_deduct(client, admin_token,
                                                    customer_with_balance,
                                                    seed_data, db_session):
    """ตรวจสอบว่าหัก session → สร้าง activity log action='customer_hour.deduct'"""
    customer_id = customer_with_balance(hours=3)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    await post(client, "/customer-hours/deduct",
               token=admin_token,
               json={"customer_id": customer_id, "branch_id": pattaya_branch_id},
               expected_status=200)

    with allure.step("Assert activity log created with action='customer_hour.deduct'"):
        assert_activity_log(db_session, action="customer_hour.deduct")


@allure.title("TC-API-LOG-05: Activity log created on order.create")
@pytest.mark.be
async def test_activity_log_created_on_order_create(client, admin_token,
                                                      create_customer, create_package,
                                                      seed_data, db_session):
    """ตรวจสอบว่าสร้าง order → สร้าง activity log action='order.create'"""
    customer_id = create_customer(branch="pattaya")
    package_id = create_package()
    pattaya_branch_id = str(seed_data["pattaya"].id)

    order_payload = build_order_payload(
        customer_id=customer_id,
        package_id=package_id,
        branch_id=pattaya_branch_id,
        hours=10,
    )

    response = await post(client, "/orders",
                          token=admin_token,
                          json=order_payload,
                          expected_status=201)

    with allure.step("Assert activity log created with action='order.create'"):
        assert_activity_log(db_session, action="order.create")


@allure.title("TC-API-LOG-06: Activity log created on order.edit")
@pytest.mark.be
async def test_activity_log_created_on_order_edit(client, admin_token,
                                                   create_order, db_session):
    """ตรวจสอบว่าแก้ไข order → สร้าง activity log action='order.edit'"""
    order_id = create_order()

    await put(client, f"/orders/{order_id}",
              token=admin_token,
              json={"notes": "updated notes for log test"},
              expected_status=200)

    with allure.step("Assert activity log created with action='order.edit'"):
        assert_activity_log(db_session, action="order.edit")


@allure.title("TC-API-LOG-07: Activity log created on booking.confirm")
@pytest.mark.be
async def test_activity_log_created_on_booking_confirm(client, admin_token,
                                                        create_booking, db_session):
    """ตรวจสอบว่า confirm booking → สร้าง activity log action='booking.confirm'"""
    booking_id = create_booking(status="pending")

    await put(client, f"/bookings/{booking_id}/confirm",
              token=admin_token,
              json={},
              expected_status=200)

    with allure.step("Assert activity log created with action='booking.confirm'"):
        assert_activity_log(db_session, action="booking.confirm")


@allure.title("TC-API-LOG-08: Activity log created on booking.cancel")
@pytest.mark.be
async def test_activity_log_created_on_booking_cancel(client, admin_token,
                                                       create_booking, db_session):
    """ตรวจสอบว่า cancel booking → สร้าง activity log action='booking.cancel'"""
    booking_id = create_booking(status="confirmed")

    await delete(client, f"/bookings/{booking_id}",
                 token=admin_token, expected_status=200)

    with allure.step("Assert activity log created with action='booking.cancel'"):
        assert_activity_log(db_session, action="booking.cancel")


@allure.title("TC-API-LOG-09: Activity log created on user.create")
@pytest.mark.be
async def test_activity_log_created_on_user_create(client, owner_token,
                                                    seed_data, db_session):
    """ตรวจสอบว่าสร้าง user → สร้าง activity log action='user.create'"""
    pattaya_branch_id = str(seed_data["pattaya"].id)

    await post(client, "/users",
               token=owner_token,
               json={
                   "username": "log_test_user",
                   "email": "log_test@test.com",
                   "password": "secure_pass",
                   "role": "ADMIN",
                   "branch_id": pattaya_branch_id,
               },
               expected_status=201)

    with allure.step("Assert activity log created with action='user.create'"):
        assert_activity_log(db_session, action="user.create")


@allure.title("TC-API-LOG-10: Activity log created on permission.update")
@pytest.mark.be
async def test_activity_log_created_on_permission_update(client, developer_token, db_session):
    """ตรวจสอบว่า update permission → สร้าง activity log action='permission.update'"""
    await put(client, "/permissions",
              token=developer_token,
              json={
                  "role": "admin",
                  "resource": "customer",
                  "action": "view",
                  "allowed": True,
              },
              expected_status=200)

    with allure.step("Assert activity log created with action='permission.update'"):
        assert_activity_log(db_session, action="permission.update")


@allure.title("TC-API-LOG-11: Activity log created on customer.edit")
@pytest.mark.be
async def test_activity_log_created_on_customer_edit(client, admin_token,
                                                      create_customer, db_session):
    """ตรวจสอบว่าแก้ไข customer → สร้าง activity log action='customer.edit'"""
    customer_id = create_customer(branch="pattaya")

    await put(client, f"/customers/{customer_id}",
              token=admin_token,
              json={"phone": "0899999999"},
              expected_status=200)

    with allure.step("Assert activity log created with action='customer.edit'"):
        assert_activity_log(db_session, action="customer.edit", target_id=customer_id)


@allure.title("TC-API-LOG-12: Activity log created on customer.delete")
@pytest.mark.be
async def test_activity_log_created_on_customer_delete(client, owner_token,
                                                        create_customer, db_session):
    """ตรวจสอบว่าลบ customer → สร้าง activity log action='customer.delete'"""
    customer_id = create_customer(branch="pattaya")

    await delete(client, f"/customers/{customer_id}",
                 token=owner_token, expected_status=204)

    with allure.step("Assert activity log created with action='customer.delete'"):
        assert_activity_log(db_session, action="customer.delete", target_id=customer_id)


@allure.title("TC-API-LOG-13: Activity log created on customer_hour.adjust")
@pytest.mark.be
async def test_activity_log_created_on_hour_adjust(client, admin_token,
                                                    customer_with_balance, db_session):
    """ตรวจสอบว่า adjust session → สร้าง activity log action='customer_hour.adjust'"""
    customer_id = customer_with_balance(hours=5)

    await put(client, "/customer-hours/adjust",
              token=admin_token,
              json={
                  "customer_id": customer_id,
                  "adjustment": 3,
                  "reason": "log test adjustment",
              },
              expected_status=200)

    with allure.step("Assert activity log created with action='customer_hour.adjust'"):
        assert_activity_log(db_session, action="customer_hour.adjust")
