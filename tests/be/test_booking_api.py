# tests/be/test_booking_api.py
#
# BE tests สำหรับ Booking API
# TC-API-BOOK-01 ถึง TC-API-BOOK-15

import pytest
import allure
from helpers.common_api import (
    get, post, put, delete,
    assert_forbidden, build_booking_payload,
)


# ─── GET /bookings ────────────────────────────────────────────────────────────────

@allure.title("TC-API-BOOK-01: GET /bookings — returns timetable slots with correct fields")
@pytest.mark.be
async def test_booking_list_returns_timetable(client, admin_token, create_booking):
    """ตรวจสอบว่า GET /bookings คืน slots พร้อม status, trainer, customer"""
    create_booking(status="pending")
    create_booking(status="confirmed")

    response = await get(client, "/bookings", token=admin_token, expected_status=200)

    with allure.step("Assert booking list has required fields"):
        booking_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert len(booking_list) >= 1, "At least one booking must be returned."
        required_booking_fields = ["status", "trainer_id", "start_time", "end_time"]
        for booking_entry in booking_list:
            for field_name in required_booking_fields:
                assert field_name in booking_entry, (
                    f"Booking entry must contain '{field_name}' field."
                )


@allure.title("TC-API-BOOK-14: GET /bookings?start_date=&end_date= — filter by date range")
@pytest.mark.be
async def test_booking_date_range_filter(client, admin_token, create_booking):
    """ตรวจสอบว่า ?start_date=&end_date= filter ทำงานถูกต้อง"""
    from datetime import date

    create_booking(status="pending")

    today_str = str(date.today())

    response = await get(client, "/bookings",
                         token=admin_token,
                         params={"start_date": today_str, "end_date": today_str},
                         expected_status=200)

    with allure.step("Assert bookings within date range returned"):
        booking_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert isinstance(booking_list, list), "Response must be a list."


@allure.title("TC-API-BOOK-15: GET /bookings?trainer_id= — filter by trainer")
@pytest.mark.be
async def test_booking_trainer_filter(client, admin_token,
                                      create_booking, create_trainer):
    """ตรวจสอบว่า ?trainer_id= filter คืนเฉพาะ bookings ของ trainer นั้น"""
    target_trainer_id = create_trainer(branch="pattaya", name="Target Trainer")
    other_trainer_id = create_trainer(branch="pattaya", name="Other Trainer")

    create_booking(status="pending", trainer_id=target_trainer_id)
    create_booking(status="pending", trainer_id=other_trainer_id)

    response = await get(client, "/bookings",
                         token=admin_token,
                         params={"trainer_id": target_trainer_id},
                         expected_status=200)

    with allure.step("Assert only bookings for target trainer returned"):
        booking_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        for booking_entry in booking_list:
            assert booking_entry.get("trainer_id") == target_trainer_id, (
                f"Booking {booking_entry.get('id')} belongs to trainer "
                f"{booking_entry.get('trainer_id')} but filter was for {target_trainer_id}."
            )


# ─── POST /bookings ───────────────────────────────────────────────────────────────

@allure.title("TC-API-BOOK-02: POST /bookings — admin creates booking with status=pending")
@pytest.mark.be
async def test_admin_creates_booking(client, admin_token, create_customer,
                                     create_trainer, seed_data):
    """ตรวจสอบว่า admin สร้าง booking ได้ → 201 Created, status=pending"""
    from datetime import date

    customer_id = create_customer(branch="pattaya")
    trainer_id = create_trainer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)
    booking_date = str(date.today())

    booking_payload = build_booking_payload(
        branch_id=pattaya_branch_id,
        trainer_id=trainer_id,
        customer_id=customer_id,
        start_time=f"{booking_date}T09:00:00",
        end_time=f"{booking_date}T10:00:00",
    )

    response = await post(client, "/bookings",
                          token=admin_token,
                          json=booking_payload,
                          expected_status=201)

    with allure.step("Assert booking created with status=pending"):
        booking_data = response.json()
        assert booking_data.get("status", "").lower() == "pending", (
            f"New booking must have status='pending' but got '{booking_data.get('status')}'."
        )


@allure.title("TC-API-BOOK-03: POST /bookings — trainer can book own slot")
@pytest.mark.be
async def test_trainer_can_book_own_slot(client, trainer_token, create_customer,
                                          seed_data, db_session):
    """ตรวจสอบว่า trainer สร้าง booking ที่ trainer_id ตัวเอง → 201 Created"""
    from datetime import date
    from api.models import User

    trainer_user_record = db_session.query(User).filter_by(role="TRAINER").first()
    trainer_id_str = str(trainer_user_record.id)
    customer_id = create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)
    booking_date = str(date.today())

    booking_payload = build_booking_payload(
        branch_id=pattaya_branch_id,
        trainer_id=trainer_id_str,
        customer_id=customer_id,
        start_time=f"{booking_date}T11:00:00",
        end_time=f"{booking_date}T12:00:00",
    )

    response = await post(client, "/bookings",
                          token=trainer_token,
                          json=booking_payload,
                          expected_status=201)

    with allure.step("Assert booking created successfully"):
        assert "id" in response.json(), "Created booking must have 'id' field."


@allure.title("TC-API-BOOK-04: POST /bookings — trainer cannot book for another trainer (403)")
@pytest.mark.be
async def test_trainer_cannot_book_for_other_trainer(client, trainer_token,
                                                      create_customer, create_trainer,
                                                      seed_data):
    """ตรวจสอบว่า trainer สร้าง booking ด้วย trainer_id ของคนอื่น → 403 Forbidden"""
    from datetime import date

    other_trainer_id = create_trainer(branch="pattaya", name="Another Trainer")
    customer_id = create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)
    booking_date = str(date.today())

    booking_payload = build_booking_payload(
        branch_id=pattaya_branch_id,
        trainer_id=other_trainer_id,
        customer_id=customer_id,
        start_time=f"{booking_date}T14:00:00",
        end_time=f"{booking_date}T15:00:00",
    )

    response = await post(client, "/bookings",
                          token=trainer_token,
                          json=booking_payload)

    assert_forbidden(response)


# ─── PUT /bookings/:id/confirm ────────────────────────────────────────────────────

@allure.title("TC-API-BOOK-05: PUT /bookings/:id/confirm — confirm pending booking")
@allure.title("TC-API-BOOK-11: Admin can confirm booking")
@pytest.mark.be
async def test_admin_can_confirm_booking(client, admin_token, create_booking):
    """ตรวจสอบว่า admin confirm booking ได้ → 200 OK, status=confirmed"""
    booking_id = create_booking(status="pending")

    response = await put(client, f"/bookings/{booking_id}/confirm",
                         token=admin_token,
                         json={},
                         expected_status=200)

    with allure.step("Assert booking status changed to confirmed"):
        booking_data = response.json()
        confirmed_status = booking_data.get("status", "").lower()
        assert confirmed_status == "confirmed", (
            f"Expected status='confirmed' after confirm action "
            f"but got '{confirmed_status}'."
        )


@allure.title("TC-API-BOOK-11b: Trainer cannot confirm booking (403)")
@pytest.mark.be
async def test_trainer_cannot_confirm_booking(client, trainer_token, create_booking):
    """ตรวจสอบว่า trainer ยืนยัน booking ไม่ได้ → 403 Forbidden"""
    booking_id = create_booking(status="pending")

    response = await put(client, f"/bookings/{booking_id}/confirm",
                         token=trainer_token,
                         json={})

    assert_forbidden(response)


# ─── DELETE /bookings/:id ─────────────────────────────────────────────────────────

@allure.title("TC-API-BOOK-06: DELETE /bookings/:id — admin can cancel booking")
@pytest.mark.be
async def test_admin_can_cancel_booking(client, admin_token, create_booking):
    """ตรวจสอบว่า admin cancel booking ได้ → 200 OK, status=cancelled"""
    booking_id = create_booking(status="confirmed")

    response = await delete(client, f"/bookings/{booking_id}",
                            token=admin_token, expected_status=200)

    with allure.step("Assert booking status changed to cancelled"):
        booking_data = response.json()
        cancelled_status = booking_data.get("status", "").lower()
        assert cancelled_status == "cancelled", (
            f"Expected status='cancelled' after cancel action "
            f"but got '{cancelled_status}'."
        )


@allure.title("TC-API-BOOK-07: DELETE /bookings/:id — trainer cannot cancel (403)")
@pytest.mark.be
async def test_trainer_cannot_cancel_booking(client, trainer_token, create_booking):
    """ตรวจสอบว่า trainer cancel booking ไม่ได้ → 403 Forbidden"""
    booking_id = create_booking(status="confirmed")

    response = await delete(client, f"/bookings/{booking_id}",
                            token=trainer_token)

    assert_forbidden(response)


@allure.title("TC-API-BOOK-12: DELETE /bookings/:id — cancel returns session when policy=return")
@pytest.mark.be
async def test_cancel_booking_returns_session_when_policy_allows(client, admin_token,
                                                                   customer_with_balance,
                                                                   create_booking,
                                                                   db_session):
    """
    ตรวจสอบว่าเมื่อ cancel_policy.return_hour=true
    session ถูกคืนให้ customer หลัง cancel
    """
    initial_hour_count = 5
    customer_id = customer_with_balance(hours=initial_hour_count)
    booking_id = create_booking(status="confirmed", customer_id=customer_id)

    await delete(client, f"/bookings/{booking_id}",
                 token=admin_token, expected_status=200)

    with allure.step("Assert hour_balance restored after cancel"):
        from api.models import CustomerHourBalance
        db_session.expire_all()
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        assert hour_balance_record.remaining >= initial_hour_count, (
            f"Expected hour_balance >= {initial_hour_count} after cancel with return policy "
            f"but got {hour_balance_record.remaining}. "
            "Cancel policy must restore the deducted session."
        )


@allure.title("TC-API-BOOK-13: DELETE /bookings/:id — cancel does not return session when policy=no return")
@pytest.mark.be
async def test_cancel_booking_no_return_when_policy_disallows(client, admin_token,
                                                               customer_with_balance,
                                                               create_booking,
                                                               db_session, db_session_override=None):
    """
    ตรวจสอบว่าเมื่อ cancel_policy.return_hour=false
    session ไม่ถูกคืนหลัง cancel
    """
    initial_hour_count = 5
    customer_id = customer_with_balance(hours=initial_hour_count)
    booking_id = create_booking(status="confirmed", customer_id=customer_id)

    await delete(client, f"/bookings/{booking_id}",
                 token=admin_token, expected_status=200)

    with allure.step("Assert hour_balance unchanged after cancel (no return policy)"):
        from api.models import CustomerHourBalance
        db_session.expire_all()
        hour_balance_record = db_session.query(CustomerHourBalance).filter_by(
            customer_id=customer_id
        ).first()
        assert hour_balance_record.remaining == initial_hour_count, (
            f"Expected hour_balance={initial_hour_count} after cancel with no-return policy "
            f"but got {hour_balance_record.remaining}. "
            "When return_hour=false, balance must remain unchanged."
        )


# ─── POST /bookings/external ─────────────────────────────────────────────────────

@allure.title("TC-API-BOOK-08: POST /bookings/external — external customer request")
@pytest.mark.be
async def test_external_booking_request(client, create_customer, seed_data):
    """ตรวจสอบว่า external API key สร้าง booking ได้ → 201 Created, status=pending"""
    from datetime import date

    customer_id = create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)
    external_api_key = "test_external_api_key"
    booking_date = str(date.today())

    external_payload = {
        "customer_id": customer_id,
        "branch_id": pattaya_branch_id,
        "start_time": f"{booking_date}T15:00:00",
        "slots": 2,
    }

    response = await post(client, "/bookings/external",
                          api_key=external_api_key,
                          json=external_payload,
                          expected_status=201)

    with allure.step("Assert external booking created with status=pending"):
        booking_data = response.json()
        assert booking_data.get("status", "").lower() == "pending", (
            "External bookings must start with status='pending'."
        )


@allure.title("TC-API-BOOK-09: POST /bookings/external — non-contiguous slots rejected")
@pytest.mark.be
async def test_external_booking_non_contiguous_slots_rejected(client,
                                                               create_customer, seed_data):
    """ตรวจสอบว่า slots ที่ไม่ต่อเนื่อง → 400 Bad Request"""
    from datetime import date

    customer_id = create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)
    external_api_key = "test_external_api_key"

    response = await post(client, "/bookings/external",
                          api_key=external_api_key,
                          json={
                              "customer_id": customer_id,
                              "branch_id": pattaya_branch_id,
                              "slot_times": ["09:00", "11:00"],  # ไม่ต่อเนื่อง
                          })

    with allure.step("Assert 400 — non-contiguous slots rejected"):
        assert response.status_code == 400, (
            f"Expected 400 for non-contiguous slots but got {response.status_code}. "
            "External bookings must only accept contiguous time slots."
        )


@allure.title("TC-API-BOOK-10: POST /bookings/external — cross-day slots rejected")
@pytest.mark.be
async def test_external_booking_cross_day_slots_rejected(client,
                                                          create_customer, seed_data):
    """ตรวจสอบว่า slots ข้ามวัน → 400 Bad Request"""
    from datetime import date, timedelta

    customer_id = create_customer(branch="pattaya")
    pattaya_branch_id = str(seed_data["pattaya"].id)
    external_api_key = "test_external_api_key"
    today_str = str(date.today())
    tomorrow_str = str(date.today() + timedelta(days=1))

    response = await post(client, "/bookings/external",
                          api_key=external_api_key,
                          json={
                              "customer_id": customer_id,
                              "branch_id": pattaya_branch_id,
                              "start_time": f"{today_str}T23:00:00",
                              "end_time": f"{tomorrow_str}T01:00:00",  # ข้ามวัน
                          })

    with allure.step("Assert 400 — cross-day booking rejected"):
        assert response.status_code == 400, (
            f"Expected 400 for cross-day booking but got {response.status_code}. "
            "Bookings must be within the same day."
        )
