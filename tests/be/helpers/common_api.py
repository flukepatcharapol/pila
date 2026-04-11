# tests/be/helpers/common_api.py
#
# Shared helper functions สำหรับ BE API tests ทั้งหมด
# ทุก test file ควร import จากที่นี่แทนการ call httpx โดยตรง
# เหตุผล: ลด redundancy, log เข้า Allure อัตโนมัติทุก request

import json
import re
import allure
import pytest
from datetime import date
from httpx import AsyncClient, Response
from typing import Any


# ─── Core Request Functions ─────────────────────────────────────────────────────

async def request(
    client: AsyncClient,
    method: str,
    url: str,
    token: str = None,
    json: dict = None,
    params: dict = None,
    expected_status: int = None,
    api_key: str = None,
) -> Response:
    """
    Core HTTP request function ที่ใช้ใน BE tests ทั้งหมด
    - Log request/response เข้า Allure อัตโนมัติ
    - ถ้าระบุ expected_status → assert ทันที

    ตัวอย่างใช้งาน:
        # ไม่ assert status (จะ assert เองทีหลัง)
        res = await request(client, "GET", "/customers", token=admin_token)

        # Assert status อัตโนมัติ
        res = await request(client, "POST", "/customers",
                            token=admin_token, json=payload, expected_status=201)
    """
    # สร้าง headers — ใส่ Authorization ถ้ามี token
    headers = {}
    if token:
        # Bearer token สำหรับ JWT ปกติ
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        # API Key สำหรับ /internal/* endpoints
        headers["X-API-Key"] = api_key

    # Log request เข้า Allure ก่อนส่ง
    _log_request(method, url, payload=json, headers=headers, params=params)

    # ส่ง HTTP request จริงผ่าน httpx AsyncClient
    # GET/DELETE ไม่รับ json body
    kwargs: dict = {"params": params, "headers": headers}
    if method.upper() not in ("GET", "DELETE", "HEAD"):
        kwargs["json"] = json
    response = await getattr(client, method.lower())(url, **kwargs)

    # Log response เข้า Allure หลังได้รับ
    _log_response(response)

    # ถ้าระบุ expected_status → assert ทันที ไม่ต้องทำใน test
    if expected_status is not None:
        assert response.status_code == expected_status, (
            f"Expected HTTP {expected_status} but got {response.status_code}.\n"
            f"URL: {method.upper()} {url}\n"
            f"Response: {response.text[:500]}"
        )

    return response


async def get(client, url, token=None, params=None, expected_status=None) -> Response:
    """Shorthand สำหรับ GET request"""
    return await request(client, "GET", url, token=token,
                         params=params, expected_status=expected_status)


async def post(client, url, token=None, json=None,
               expected_status=None, api_key=None) -> Response:
    """Shorthand สำหรับ POST request"""
    return await request(client, "POST", url, token=token,
                         json=json, expected_status=expected_status, api_key=api_key)


async def put(client, url, token=None, json=None, expected_status=None) -> Response:
    """Shorthand สำหรับ PUT request"""
    return await request(client, "PUT", url, token=token,
                         json=json, expected_status=expected_status)


async def delete(client, url, token=None, expected_status=None) -> Response:
    """Shorthand สำหรับ DELETE request"""
    return await request(client, "DELETE", url, token=token,
                         expected_status=expected_status)


# ─── Assertion Helpers ──────────────────────────────────────────────────────────

def assert_pagination(data: dict, expected_page: int = 1) -> None:
    """
    ตรวจสอบว่า response มี pagination fields ครบถ้วน
    ใช้กับทุก list endpoint ที่ return paginated response
    """
    with allure.step("Assert pagination structure"):
        # ต้องมี fields เหล่านี้ทุก paginated response
        assert "items" in data, "Paginated response must have 'items' field"
        assert "total" in data, "Paginated response must have 'total' field"
        assert "page" in data, "Paginated response must have 'page' field"
        assert isinstance(data["items"], list), "'items' must be a list"
        assert data["page"] == expected_page, (
            f"Expected page {expected_page} but got {data['page']}"
        )


def assert_no_uuid_in_display_fields(items: list, fields: list) -> None:
    """
    ตรวจสอบว่าไม่มี UUID ใน display fields ของ list items
    ป้องกัน bug จากระบบเก่าที่ return UUID แทนชื่อจริง

    ตัวอย่าง:
        assert_no_uuid_in_display_fields(data["items"],
                                         fields=["name", "nickname", "trainer_name"])
    """
    # UUID format: 8-4-4-4-12 hex characters
    uuid_pattern = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.IGNORECASE
    )

    with allure.step(f"Assert no UUIDs in display fields: {fields}"):
        for item in items:
            for field in fields:
                value = item.get(field, "")
                if value and isinstance(value, str):
                    assert not uuid_pattern.search(value), (
                        f"Field '{field}' contains a raw UUID: '{value}'. "
                        "Display fields must show human-readable values, not UUIDs."
                    )


def assert_branch_scope(items: list, expected_branch_id: str) -> None:
    """
    ตรวจสอบว่าทุก item ใน list อยู่ใน branch ที่ถูกต้อง
    ใช้ตรวจสอบ branch isolation ของแต่ละ role

    ตัวอย่าง:
        assert_branch_scope(data["items"], expected_branch_id=pattaya_id)
    """
    with allure.step(f"Assert all items belong to branch {expected_branch_id}"):
        for item in items:
            assert item.get("branch_id") == expected_branch_id, (
                f"Item {item.get('id')} belongs to branch {item.get('branch_id')} "
                f"but should only be in branch {expected_branch_id}. "
                "Branch isolation is broken — admin/trainer is seeing other branch data."
            )


def assert_forbidden(response: Response) -> None:
    """ตรวจสอบว่า response เป็น 403 Forbidden"""
    with allure.step("Assert 403 Forbidden"):
        assert response.status_code == 403, (
            f"Expected 403 Forbidden but got {response.status_code}. "
            "This endpoint should be blocked for this role."
        )


def assert_not_found(response: Response) -> None:
    """ตรวจสอบว่า response เป็น 404 Not Found"""
    with allure.step("Assert 404 Not Found"):
        assert response.status_code == 404, (
            f"Expected 404 Not Found but got {response.status_code}."
        )


def assert_validation_error(response: Response) -> None:
    """ตรวจสอบว่า response เป็น 422 Unprocessable Entity"""
    with allure.step("Assert 422 Validation Error"):
        assert response.status_code == 422, (
            f"Expected 422 Unprocessable Entity but got {response.status_code}. "
            "Invalid input should be rejected with 422."
        )


def assert_conflict(response: Response, expected_detail: str = None) -> None:
    """ตรวจสอบว่า response เป็น 409 Conflict"""
    with allure.step("Assert 409 Conflict"):
        assert response.status_code == 409, (
            f"Expected 409 Conflict but got {response.status_code}."
        )
        if expected_detail:
            assert expected_detail in response.json().get("detail", ""), (
                f"Expected detail to contain '{expected_detail}' "
                f"but got '{response.json().get('detail')}'"
            )


def assert_activity_log(db_session, action: str, target_id: str = None) -> None:
    """
    ตรวจสอบว่า activity log ถูกสร้างหลังจาก action นั้นๆ
    ใช้ตรวจสอบว่า write operations สร้าง log ถูกต้อง

    ตัวอย่าง:
        assert_activity_log(db_session, action="customer.create", target_id=customer_id)
    """
    from api.models.activity_log import ActivityLog

    with allure.step(f"Assert activity log created: action='{action}'"):
        # Query หา log ล่าสุดที่ตรงกับ action
        query = db_session.query(ActivityLog).filter(ActivityLog.action == action)
        if target_id:
            query = query.filter(ActivityLog.target_id == target_id)

        log = query.order_by(ActivityLog.created_at.desc()).first()

        assert log is not None, (
            f"No activity log found with action='{action}'. "
            "All write operations must create an activity log entry for audit purposes."
        )


# ─── Common Payload Builders ────────────────────────────────────────────────────

def build_customer_payload(
    branch_id: str,
    source_type_id: str,
    first_name: str = "Test",
    last_name: str = "Customer",
    **kwargs
) -> dict:
    """
    สร้าง payload สำหรับ POST /customers
    ใช้ใน tests หลายแห่งเพื่อลด duplication

    ตัวอย่าง:
        payload = build_customer_payload(
            branch_id=pattaya_id,
            source_type_id=mkt_source_id,
            trainer_id=trainer_id,
        )
    """
    return {
        "branch_id": branch_id,
        "source_type_id": source_type_id,
        "first_name": first_name,
        "last_name": last_name,
        "nickname": kwargs.get("nickname", "TestNick"),
        "contact_channel": kwargs.get("contact_channel", "PHONE"),
        "phone": kwargs.get("phone", "0812345678"),
        "status": kwargs.get("status", "ACTIVE"),
        "trainer_id": kwargs.get("trainer_id"),
        "caretaker_id": kwargs.get("caretaker_id"),
        "email": kwargs.get("email"),
        "line_id": kwargs.get("line_id"),
        "birthday": kwargs.get("birthday"),
        "notes": kwargs.get("notes"),
    }


def build_order_payload(
    customer_id: str,
    package_id: str,
    branch_id: str,
    hours: int = 10,
    bonus_hours: int = 0,
    total_price: float = 5000.0,
    **kwargs
) -> dict:
    """
    สร้าง payload สำหรับ POST /orders
    ใช้ใน tests หลายแห่งเพื่อลด duplication
    """
    return {
        "customer_id": customer_id,
        "package_id": package_id,
        "branch_id": branch_id,
        "order_date": str(date.today()),
        "hours": hours,
        "bonus_hours": bonus_hours,
        "payment_method": kwargs.get("payment_method", "BANK_TRANSFER"),
        "total_price": total_price,
        "price_per_session": kwargs.get("price_per_session"),
        "trainer_id": kwargs.get("trainer_id"),
        "caretaker_id": kwargs.get("caretaker_id"),
        "is_renewal": kwargs.get("is_renewal", False),
        "notes": kwargs.get("notes"),
    }


def build_booking_payload(
    branch_id: str,
    trainer_id: str,
    start_time: str,
    end_time: str,
    customer_id: str = None,
    **kwargs
) -> dict:
    """สร้าง payload สำหรับ POST /bookings"""
    return {
        "branch_id": branch_id,
        "trainer_id": trainer_id,
        "customer_id": customer_id,
        "start_time": start_time,
        "end_time": end_time,
        "booking_type": kwargs.get("booking_type", "CUSTOMER"),
        "notes": kwargs.get("notes"),
    }


# ─── Allure Logging (Internal) ──────────────────────────────────────────────────

def _log_request(method: str, url: str, payload: dict = None,
                 headers: dict = None, params: dict = None) -> None:
    """Internal: Log request เข้า Allure"""
    with allure.step(f"→ {method.upper()} {url}"):
        if payload:
            allure.attach(
                body=json.dumps(payload, ensure_ascii=False, indent=2),
                name="Request Body",
                attachment_type=allure.attachment_type.JSON,
            )
        if params:
            allure.attach(
                body=json.dumps(params, indent=2),
                name="Query Params",
                attachment_type=allure.attachment_type.JSON,
            )
        if headers:
            # ซ่อน Authorization value เพื่อ security
            safe = {k: "***" if k.lower() == "authorization" else v
                    for k, v in headers.items()}
            allure.attach(
                body=json.dumps(safe, indent=2),
                name="Headers",
                attachment_type=allure.attachment_type.JSON,
            )


def _log_response(response: Response) -> None:
    """Internal: Log response เข้า Allure"""
    with allure.step(f"← {response.status_code}"):
        try:
            body = response.json()
            body_str = json.dumps(body, ensure_ascii=False, indent=2)
            attachment_type = allure.attachment_type.JSON
        except Exception:
            body_str = response.text
            attachment_type = allure.attachment_type.TEXT

        allure.attach(
            body=body_str,
            name=f"Response ({response.status_code})",
            attachment_type=attachment_type,
        )
