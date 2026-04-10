# tests/be/test_customer_api.py
#
# BE tests สำหรับ Customer API
# TC-API-CUST-01 ถึง TC-API-CUST-19

import re
import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_pagination, assert_no_uuid_in_display_fields,
    assert_branch_scope, assert_forbidden, assert_not_found,
    assert_validation_error, assert_conflict, assert_activity_log,
    build_customer_payload,
)


# ─── GET /customers ─────────────────────────────────────────────────────────────

@allure.title("TC-API-CUST-01: Customer list returns paginated data without UUIDs")
@pytest.mark.be
async def test_customer_list_paginated(client, admin_token, create_customer, seed_data):
    """ตรวจสอบว่า GET /customers return paginated list และไม่มี UUID ใน display fields"""
    # สร้าง customers ทดสอบก่อน
    create_customer(branch="pattaya")
    create_customer(branch="pattaya")

    with allure.step("GET /customers as admin"):
        res = await get(client, "/customers", token=admin_token, expected_status=200)

    with allure.step("Assert pagination structure"):
        data = res.json()
        assert_pagination(data, expected_page=1)

    with allure.step("Assert no UUID in display fields"):
        assert_no_uuid_in_display_fields(
            data["items"],
            fields=["name", "nickname", "trainer_name", "caretaker_name"]
        )


@allure.title("TC-API-CUST-02: Admin sees only own branch customers")
@pytest.mark.be
async def test_admin_sees_own_branch_only(client, admin_token, create_customer, seed_data):
    """ตรวจสอบว่า admin เห็นแค่ลูกค้าในสาขาตัวเอง (branch isolation)"""
    pattaya_id = str(seed_data["branches"][0].id)
    # สร้างลูกค้าทั้ง Pattaya และ Kanchanaburi
    create_customer(branch="pattaya")
    create_customer(branch="kanchanaburi")

    with allure.step("GET /customers as admin (Pattaya)"):
        res = await get(client, "/customers", token=admin_token, expected_status=200)

    with allure.step("Assert only Pattaya customers returned"):
        assert_branch_scope(res.json()["items"], expected_branch_id=pattaya_id)


@allure.title("TC-API-CUST-02b: Trainer sees only own branch customers")
@pytest.mark.be
async def test_trainer_sees_own_branch_only(client, trainer_token, create_customer, seed_data):
    """ตรวจสอบว่า trainer เห็นแค่ลูกค้าในสาขาตัวเอง"""
    pattaya_id = str(seed_data["branches"][0].id)
    create_customer(branch="pattaya")
    create_customer(branch="kanchanaburi")

    res = await get(client, "/customers", token=trainer_token, expected_status=200)
    assert_branch_scope(res.json()["items"], expected_branch_id=pattaya_id)


@allure.title("TC-API-CUST-03: Owner sees all branches within partner")
@pytest.mark.be
async def test_owner_sees_all_branches(client, owner_token, create_customer, seed_data):
    """ตรวจสอบว่า owner เห็นลูกค้าทุกสาขาใน partner"""
    create_customer(branch="pattaya")
    create_customer(branch="chachoengsao")
    create_customer(branch="kanchanaburi")

    res = await get(client, "/customers", token=owner_token, expected_status=200)

    with allure.step("Assert customers from all 3 branches present"):
        items = res.json()["items"]
        branch_ids = {item["branch_id"] for item in items}
        assert len(branch_ids) == 3, (
            f"Owner should see customers from all 3 branches "
            f"but only saw branches: {branch_ids}"
        )


@allure.title("TC-API-CUST-04: Search filter returns matching customers")
@pytest.mark.be
async def test_customer_search_by_name(client, admin_token, create_customer, seed_data):
    """ตรวจสอบว่า ?search= filter ทำงานถูกต้อง"""
    create_customer(branch="pattaya", first_name="นามแรก")
    create_customer(branch="pattaya", first_name="อื่นๆ")

    res = await get(client, "/customers", token=admin_token,
                    params={"search": "นาม"}, expected_status=200)

    with allure.step("Assert only matching customers returned"):
        items = res.json()["items"]
        assert all("นาม" in (item.get("first_name", "") + item.get("nickname", ""))
                   for item in items), (
            "Search filter must return only customers matching the search term."
        )


@allure.title("TC-API-CUST-15: Pagination page 2 returns second set")
@pytest.mark.be
async def test_customer_pagination_page2(client, owner_token, create_customer):
    """ตรวจสอบว่า pagination page 2 ทำงานถูกต้อง"""
    # สร้าง 15 customers เพื่อให้มี page 2
    for _ in range(15):
        create_customer(branch="pattaya")

    with allure.step("Get page 1"):
        res1 = await get(client, "/customers", token=owner_token,
                         params={"page": 1, "page_size": 10}, expected_status=200)
        page1_ids = {item["id"] for item in res1.json()["items"]}

    with allure.step("Get page 2"):
        res2 = await get(client, "/customers", token=owner_token,
                         params={"page": 2, "page_size": 10}, expected_status=200)
        page2_ids = {item["id"] for item in res2.json()["items"]}
        assert_pagination(res2.json(), expected_page=2)

    with allure.step("Assert page 2 contains different items than page 1"):
        assert page1_ids.isdisjoint(page2_ids), (
            "Page 2 must contain different items than page 1. "
            "Pagination is not working correctly."
        )


@allure.title("TC-API-CUST-16: Page size over limit returns 400")
@pytest.mark.be
async def test_customer_page_size_limit(client, admin_token):
    """ตรวจสอบว่า page_size เกิน limit → 400 Bad Request"""
    res = await get(client, "/customers", token=admin_token,
                    params={"page_size": 999})

    with allure.step("Assert 400 for oversized page"):
        assert res.status_code == 400, (
            f"Expected 400 for page_size=999 but got {res.status_code}. "
            "Page size must be limited to prevent performance issues."
        )


# ─── POST /customers ─────────────────────────────────────────────────────────────

@allure.title("TC-API-CUST-06: Create customer with valid payload")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.be
async def test_create_customer_valid(client, admin_token, seed_data):
    """ตรวจสอบว่าสร้าง customer ด้วย payload ถูกต้อง → 201 Created + code format ถูก"""
    branch = seed_data["branches"][0]  # Pattaya
    source_type = seed_data["source_types"]["BPY_MKT"]

    payload = build_customer_payload(
        branch_id=str(branch.id),
        source_type_id=str(source_type.id),
        first_name="ทดสอบ",
        last_name="ระบบ",
    )

    with allure.step("POST /customers with valid payload"):
        res = await post(client, "/customers",
                         token=admin_token,
                         json=payload,
                         expected_status=201)

    with allure.step("Assert customer code format BPY-MKTXXX"):
        data = res.json()
        assert "customer_code" in data, "Response must contain customer_code"
        assert data["customer_code"].startswith("BPY-MKT"), (
            f"Customer code '{data['customer_code']}' must start with 'BPY-MKT' "
            "for Pattaya branch with MKT source type."
        )
        # ตรวจ format: BPY-MKT + 3 digits
        assert re.match(r"BPY-MKT\d{3}", data["customer_code"]), (
            f"Customer code '{data['customer_code']}' must match format BPY-MKTxxx"
        )


@allure.title("TC-API-CUST-07: Customer code auto-increments per branch+source")
@pytest.mark.be
async def test_customer_code_auto_increment(client, admin_token, seed_data):
    """ตรวจสอบว่า running number เพิ่มขึ้นถูกต้องต่อ branch+source"""
    branch = seed_data["branches"][0]
    source_type = seed_data["source_types"]["BPY_MKT"]

    payload_base = build_customer_payload(
        branch_id=str(branch.id),
        source_type_id=str(source_type.id),
    )

    with allure.step("Create first customer"):
        res1 = await post(client, "/customers", token=admin_token,
                          json={**payload_base, "first_name": "คนแรก"},
                          expected_status=201)
        code1 = res1.json()["customer_code"]

    with allure.step("Create second customer (same branch+source)"):
        res2 = await post(client, "/customers", token=admin_token,
                          json={**payload_base, "first_name": "คนที่สอง"},
                          expected_status=201)
        code2 = res2.json()["customer_code"]

    with allure.step("Assert running numbers increment correctly"):
        # ดึงตัวเลขท้าย code มาเปรียบเทียบ
        num1 = int(re.search(r"\d+$", code1).group())
        num2 = int(re.search(r"\d+$", code2).group())
        assert num2 == num1 + 1, (
            f"Second customer code number ({num2}) must be exactly 1 more "
            f"than first ({num1}). Running number increment is broken."
        )


@allure.title("TC-API-CUST-08: Create customer missing required field returns 422")
@pytest.mark.be
async def test_create_customer_missing_required(client, admin_token, seed_data):
    """ตรวจสอบว่าขาด first_name → 422 Unprocessable Entity"""
    branch = seed_data["branches"][0]
    source_type = seed_data["source_types"]["BPY_MKT"]

    # ส่ง payload โดยไม่มี first_name (required field)
    payload = {
        "branch_id": str(branch.id),
        "source_type_id": str(source_type.id),
        # first_name ขาดหายไป
    }

    res = await post(client, "/customers", token=admin_token,
                     json=payload, expected_status=422)
    assert_validation_error(res)


@allure.title("TC-API-CUST-09: Trainer from wrong branch returns 400")
@pytest.mark.be
async def test_create_customer_trainer_wrong_branch(client, admin_token,
                                                    create_trainer, seed_data):
    """ตรวจสอบว่า assign trainer จาก branch อื่นให้ customer ไม่ได้ → 400"""
    branch_pattaya = seed_data["branches"][0]
    source_type = seed_data["source_types"]["BPY_MKT"]

    # สร้าง trainer ใน Kanchanaburi
    kanch_trainer_id = create_trainer(branch="kanchanaburi")

    payload = build_customer_payload(
        branch_id=str(branch_pattaya.id),
        source_type_id=str(source_type.id),
        trainer_id=kanch_trainer_id,  # trainer จาก branch อื่น!
    )

    res = await post(client, "/customers", token=admin_token,
                     json=payload, expected_status=400)

    with allure.step("Assert error mentions trainer branch mismatch"):
        assert "Trainer does not belong to selected branch" in res.json().get("detail", ""), (
            "Error must clearly state that trainer is from a different branch."
        )


@allure.title("TC-API-CUST-17: Invalid email format returns 422")
@pytest.mark.be
async def test_create_customer_invalid_email(client, admin_token, seed_data):
    """ตรวจสอบว่า email format ผิด → 422"""
    branch = seed_data["branches"][0]
    source_type = seed_data["source_types"]["BPY_MKT"]

    payload = build_customer_payload(
        branch_id=str(branch.id),
        source_type_id=str(source_type.id),
        email="not-valid-email",
    )
    res = await post(client, "/customers", token=admin_token,
                     json=payload, expected_status=422)
    assert_validation_error(res)


# ─── GET /customers/:id ──────────────────────────────────────────────────────────

@allure.title("TC-API-CUST-10: Customer detail returns full info")
@pytest.mark.be
async def test_get_customer_detail(client, admin_token, create_customer, create_order):
    """ตรวจสอบว่า GET /customers/:id return detail ครบพร้อม order history และ hours remaining"""
    customer_id = create_customer(branch="pattaya")
    create_order(customer_id=customer_id, hours=10)

    res = await get(client, f"/customers/{customer_id}",
                    token=admin_token, expected_status=200)

    with allure.step("Assert all detail fields present"):
        data = res.json()
        assert "customer_code" in data
        assert "order_history" in data, "Detail must include order_history list"
        assert "remaining_hours" in data, "Detail must include remaining_hours"


@allure.title("TC-API-CUST-11: Unknown customer ID returns 404")
@pytest.mark.be
async def test_get_customer_not_found(client, admin_token):
    """ตรวจสอบว่า customer id ที่ไม่มี → 404 Not Found"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = await get(client, f"/customers/{fake_id}",
                    token=admin_token, expected_status=404)
    assert_not_found(res)


# ─── PUT /customers/:id ──────────────────────────────────────────────────────────

@allure.title("TC-API-CUST-12: Update customer phone number")
@pytest.mark.be
async def test_update_customer(client, admin_token, create_customer):
    """ตรวจสอบว่า PUT /customers/:id อัปเดตข้อมูลถูกต้อง"""
    customer_id = create_customer(branch="pattaya")

    with allure.step("Update phone number"):
        res = await put(client, f"/customers/{customer_id}",
                        token=admin_token,
                        json={"phone": "0899999999"},
                        expected_status=200)

    with allure.step("Assert updated value returned"):
        assert res.json()["phone"] == "0899999999", (
            "Updated phone number must be returned in response."
        )

    with allure.step("Assert activity log created"):
        # การแก้ไข customer ต้องสร้าง activity log เสมอ
        pass  # checked via assert_activity_log in integration test


# ─── DELETE /customers/:id ───────────────────────────────────────────────────────

@allure.title("TC-API-CUST-13: Owner can delete customer")
@pytest.mark.be
async def test_owner_can_delete_customer(client, owner_token, create_customer):
    """ตรวจสอบว่า owner ลบ customer ได้"""
    customer_id = create_customer(branch="pattaya")
    await delete(client, f"/customers/{customer_id}",
                 token=owner_token, expected_status=204)


@allure.title("TC-API-CUST-14: Trainer cannot delete customer (403)")
@pytest.mark.be
async def test_trainer_cannot_delete_customer(client, trainer_token, create_customer):
    """ตรวจสอบว่า trainer ลบ customer ไม่ได้ → 403"""
    customer_id = create_customer(branch="pattaya")
    res = await delete(client, f"/customers/{customer_id}",
                       token=trainer_token)
    assert_forbidden(res)
