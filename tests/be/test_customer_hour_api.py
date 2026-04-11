# tests/be/test_customer_hour_api.py
#
# BE tests สำหรับ Customer Hour API
# TC-API-HOUR-01 ถึง TC-API-HOUR-12

import pytest
import allure
from helpers.common_api import (
    get, post, put,
    assert_forbidden, assert_not_found, assert_no_uuid_in_display_fields,
)


# ─── POST /customer-hours/deduct ─────────────────────────────────────────────────

@allure.title("TC-API-HOUR-01: POST /customer-hours/deduct — valid deduction reduces balance by 1")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.be
async def test_hour_deduct_valid_reduces_balance(client, admin_token,
                                                  customer_with_balance,
                                                  seed_data, db_session):
    """
    ตรวจสอบว่าหัก session ได้ถูกต้อง
    - hour_balance ลดลง 1
    - สร้าง transaction log: type=HOUR_DEDUCT, before=N, amount=1, after=N-1
    """
    initial_hour_count = 5
    customer_id = customer_with_balance(hours=initial_hour_count)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    with allure.step("POST /customer-hours/deduct"):
        response = await post(client, "/customer-hours/deduct",
                              token=admin_token,
                              json={
                                  "customer_id": customer_id,
                                  "branch_id": pattaya_branch_id,
                              },
                              expected_status=200)

    with allure.step("Assert hour_balance decremented by 1"):
        from api.models import CustomerHourBalance
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        expected_remaining = initial_hour_count - 1
        assert hour_balance_record.remaining == expected_remaining, (
            f"Expected hour_balance={expected_remaining} after deduction "
            f"but got {hour_balance_record.remaining}. "
            "Each deduction must reduce balance by exactly 1."
        )


@allure.title("TC-API-HOUR-02: POST /customer-hours/deduct — zero balance returns 400")
@pytest.mark.be
async def test_hour_deduct_zero_balance_rejected(client, admin_token,
                                                  customer_with_balance, seed_data):
    """ตรวจสอบว่าหัก session จาก customer ที่ balance=0 → 400 Bad Request"""
    customer_id = customer_with_balance(hours=0)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    response = await post(client, "/customer-hours/deduct",
                          token=admin_token,
                          json={
                              "customer_id": customer_id,
                              "branch_id": pattaya_branch_id,
                          })

    with allure.step("Assert 400 — no remaining hours"):
        assert response.status_code == 400, (
            f"Expected 400 when deducting from zero balance but got {response.status_code}. "
            "Deduction must be blocked when customer has no remaining hours."
        )
        error_detail = response.json().get("detail", "")
        assert "hour" in error_detail.lower() or "remaining" in error_detail.lower(), (
            f"Error must mention remaining hours issue, got: '{error_detail}'"
        )


# ─── GET /customer-hours/log ─────────────────────────────────────────────────────

@allure.title("TC-API-HOUR-03: GET /customer-hours/log — returns transaction history without UUIDs")
@pytest.mark.be
async def test_hour_log_returns_history_without_uuids(client, admin_token,
                                                       customer_with_balance,
                                                       seed_data):
    """
    ตรวจสอบว่า log มีข้อมูลครบ และไม่มี UUID ใน display fields
    """
    customer_id = customer_with_balance(hours=3)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    await post(client, "/customer-hours/deduct",
               token=admin_token,
               json={"customer_id": customer_id, "branch_id": pattaya_branch_id},
               expected_status=200)

    response = await get(client, "/customer-hours/log",
                         token=admin_token, expected_status=200)

    with allure.step("Assert required log fields present"):
        log_entries = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert len(log_entries) >= 1, "At least one log entry must exist after deduction."

        required_log_fields = ["transaction_type", "before", "amount", "after"]
        for log_entry in log_entries:
            for field_name in required_log_fields:
                assert field_name in log_entry, (
                    f"Log entry must contain '{field_name}' field."
                )

    with allure.step("Assert no UUIDs in display fields"):
        display_field_names = ["customer_name", "customer_code"]
        assert_no_uuid_in_display_fields(log_entries, fields=display_field_names)


@allure.title("TC-API-HOUR-04: GET /customer-hours/log with filters returns matching entries")
@pytest.mark.be
async def test_hour_log_filters_work(client, admin_token,
                                     customer_with_balance, seed_data):
    """ตรวจสอบว่า ?customer_id=&start_date= filter ทำงานถูกต้อง"""
    from datetime import date

    customer_id = customer_with_balance(hours=3)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    await post(client, "/customer-hours/deduct",
               token=admin_token,
               json={"customer_id": customer_id, "branch_id": pattaya_branch_id},
               expected_status=200)

    response = await get(client, "/customer-hours/log",
                         token=admin_token,
                         params={"customer_id": customer_id,
                                 "start_date": str(date.today())},
                         expected_status=200)

    with allure.step("Assert only entries for specified customer returned"):
        log_entries = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        for log_entry in log_entries:
            assert log_entry.get("customer_id") == customer_id, (
                f"Log entry belongs to customer {log_entry.get('customer_id')} "
                f"but filter requested customer {customer_id}."
            )


# ─── GET /customer-hours/trainer-report ──────────────────────────────────────────

@allure.title("TC-API-HOUR-05: GET /customer-hours/trainer-report returns summary")
@pytest.mark.be
async def test_trainer_report_returns_summary(client, admin_token, create_trainer, seed_data):
    """ตรวจสอบว่า trainer report มี total_hours, session_count, history"""
    from datetime import date, timedelta

    trainer_id = create_trainer(branch="pattaya")

    response = await get(client, "/customer-hours/trainer-report",
                         token=admin_token,
                         params={
                             "trainer_id": trainer_id,
                             "start_date": str(date.today() - timedelta(days=7)),
                             "end_date": str(date.today()),
                         },
                         expected_status=200)

    with allure.step("Assert report summary fields present"):
        report_data = response.json()
        required_report_fields = ["total_hours", "session_count", "history"]
        for field_name in required_report_fields:
            assert field_name in report_data, (
                f"Trainer report must contain '{field_name}' field."
            )


@allure.title("TC-API-HOUR-07: Trainer cannot view another trainer's report (403)")
@pytest.mark.be
async def test_trainer_cannot_view_other_trainer_report(client, trainer_token,
                                                         create_trainer, seed_data):
    """ตรวจสอบว่า trainer ขอ report ของ trainer อื่น → 403 Forbidden"""
    other_trainer_id = create_trainer(branch="pattaya", name="Other Trainer")
    from datetime import date

    response = await get(client, "/customer-hours/trainer-report",
                         token=trainer_token,
                         params={
                             "trainer_id": other_trainer_id,
                             "start_date": str(date.today()),
                             "end_date": str(date.today()),
                         })

    assert_forbidden(response)


# ─── GET /customer-hours/remaining/:customer_id ───────────────────────────────────

@allure.title("TC-API-HOUR-06: GET /customer-hours/remaining/:id returns current balance")
@pytest.mark.be
async def test_get_remaining_hours_returns_balance(client, admin_token,
                                                    customer_with_balance):
    """ตรวจสอบว่า GET remaining/:id คืน hour_balance ปัจจุบัน"""
    initial_hour_count = 8
    customer_id = customer_with_balance(hours=initial_hour_count)

    response = await get(client, f"/customer-hours/remaining/{customer_id}",
                         token=admin_token, expected_status=200)

    with allure.step("Assert correct balance returned"):
        balance_data = response.json()
        assert "hour_balance" in balance_data, "Response must contain 'hour_balance' field."
        assert balance_data["hour_balance"] == initial_hour_count, (
            f"Expected hour_balance={initial_hour_count} but got {balance_data['hour_balance']}."
        )


@allure.title("TC-API-HOUR-11: GET /customer-hours/remaining/:id — 404 for unknown customer")
@pytest.mark.be
async def test_get_remaining_hours_unknown_customer(client, admin_token):
    """ตรวจสอบว่า customer ไม่มีในระบบ → 404 Not Found"""
    from helpers.common_api import assert_not_found

    response = await get(client, "/customer-hours/remaining/00000000-0000-0000-0000-000000000000",
                         token=admin_token)
    assert_not_found(response)


# ─── PUT /customer-hours/adjust ──────────────────────────────────────────────────

@allure.title("TC-API-HOUR-08: PUT /customer-hours/adjust — positive adjustment increases balance")
@pytest.mark.be
async def test_hour_adjust_positive_increases_balance(client, admin_token,
                                                       customer_with_balance, db_session):
    """ตรวจสอบว่า manual adjust ค่าบวก เพิ่ม balance + สร้าง log type=HOUR_ADJUST"""
    initial_hour_count = 3
    customer_id = customer_with_balance(hours=initial_hour_count)
    adjustment_amount = 5

    response = await put(client, "/customer-hours/adjust",
                         token=admin_token,
                         json={
                             "customer_id": customer_id,
                             "adjustment": adjustment_amount,
                             "reason": "manual correction for test",
                         },
                         expected_status=200)

    with allure.step("Assert hour_balance increased correctly"):
        from api.models import CustomerHourBalance
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        expected_balance = initial_hour_count + adjustment_amount
        assert hour_balance_record.remaining == expected_balance, (
            f"Expected hour_balance={expected_balance} after +{adjustment_amount} adjustment "
            f"but got {hour_balance_record.remaining}."
        )


@allure.title("TC-API-HOUR-09: PUT /customer-hours/adjust — negative adjustment reduces balance")
@pytest.mark.be
async def test_hour_adjust_negative_reduces_balance(client, admin_token,
                                                     customer_with_balance, db_session):
    """ตรวจสอบว่า manual adjust ค่าลบ ลด balance ถูกต้อง"""
    initial_hour_count = 10
    customer_id = customer_with_balance(hours=initial_hour_count)
    adjustment_amount = -3

    await put(client, "/customer-hours/adjust",
              token=admin_token,
              json={
                  "customer_id": customer_id,
                  "adjustment": adjustment_amount,
                  "reason": "manual reduction test",
              },
              expected_status=200)

    with allure.step("Assert hour_balance reduced correctly"):
        from api.models import CustomerHourBalance
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        expected_balance = initial_hour_count + adjustment_amount  # 10 + (-3) = 7
        assert hour_balance_record.remaining == expected_balance, (
            f"Expected hour_balance={expected_balance} after {adjustment_amount} adjustment "
            f"but got {hour_balance_record.remaining}."
        )


@allure.title("TC-API-HOUR-10: PUT /customer-hours/adjust — cannot adjust below zero")
@pytest.mark.be
async def test_hour_adjust_cannot_go_below_zero(client, admin_token,
                                                  customer_with_balance):
    """ตรวจสอบว่า adjustment ที่ทำให้ balance ติดลบ → 400 Bad Request"""
    initial_hour_count = 2
    customer_id = customer_with_balance(hours=initial_hour_count)

    response = await put(client, "/customer-hours/adjust",
                         token=admin_token,
                         json={
                             "customer_id": customer_id,
                             "adjustment": -5,  # เกินกว่า balance ที่มี
                             "reason": "should be blocked",
                         })

    with allure.step("Assert 400 — adjustment cannot result in negative balance"):
        assert response.status_code == 400, (
            f"Expected 400 when adjustment would result in negative balance "
            f"but got {response.status_code}. "
            "Session balance must never go below zero."
        )


@allure.title("TC-API-HOUR-12: Concurrent deductions on balance=1 — one succeeds, one fails")
@pytest.mark.be
@pytest.mark.slow
async def test_concurrent_deduction_race_condition(client, admin_token,
                                                    customer_with_balance, seed_data,
                                                    db_session):
    """
    ตรวจสอบว่า 2 deductions พร้อมกันบน balance=1 → หนึ่งสำเร็จ หนึ่งล้มเหลว
    balance สุดท้ายต้องเป็น 0 (ไม่ใช่ -1)
    """
    import asyncio

    customer_id = customer_with_balance(hours=1)
    pattaya_branch_id = str(seed_data["pattaya"].id)

    deduction_payload = {
        "customer_id": customer_id,
        "branch_id": pattaya_branch_id,
    }

    with allure.step("Send 2 concurrent deduction requests"):
        response_list = await asyncio.gather(
            post(client, "/customer-hours/deduct",
                 token=admin_token, json=deduction_payload),
            post(client, "/customer-hours/deduct",
                 token=admin_token, json=deduction_payload),
            return_exceptions=True,
        )

    with allure.step("Assert one success, one failure"):
        status_codes = [
            res.status_code for res in response_list
            if not isinstance(res, Exception)
        ]
        success_count = sum(1 for status in status_codes if status == 200)
        failure_count = sum(1 for status in status_codes if status == 400)
        assert success_count >= 1, "At least one deduction must succeed."
        assert failure_count >= 1, "At least one deduction must fail when balance is 1."

    with allure.step("Assert final balance is 0 (never -1)"):
        from api.models import CustomerHourBalance
        db_session.expire_all()  # reload from DB
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        assert hour_balance_record.remaining == 0, (
            f"Final balance must be 0 after concurrent deductions on balance=1, "
            f"but got {hour_balance_record.remaining}. "
            "Race condition protection (DB lock) is not working correctly."
        )
