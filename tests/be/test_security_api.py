# tests/be/test_security_api.py
#
# BE tests สำหรับ Security
# TC-API-SEC-01 ถึง TC-API-SEC-03

import pytest
import allure
from helpers.common_api import get, post


@allure.title("TC-API-SEC-01: SQL Injection — query param sanitized")
@pytest.mark.be
@pytest.mark.security
async def test_sql_injection_in_query_param_sanitized(client, admin_token):
    """
    ตรวจสอบว่า SQL Injection ใน query param ไม่ทำลาย DB
    ระบบต้องไม่ return error 500 หรือ drop table
    """
    sql_injection_payload = "'; DROP TABLE customers; --"

    response = await get(client, "/customers",
                         token=admin_token,
                         params={"search": sql_injection_payload})

    with allure.step("Assert no DB error — response is 200 or 400, never 500"):
        assert response.status_code in (200, 400), (
            f"Expected 200 or 400 for SQL injection attempt but got {response.status_code}. "
            "Internal server errors (500) when injecting SQL indicate possible vulnerability."
        )

    with allure.step("Assert customers table still exists (no drop happened)"):
        verify_response = await get(client, "/customers",
                                    token=admin_token,
                                    expected_status=200)
        assert "items" in verify_response.json() or isinstance(verify_response.json(), list), (
            "Customer table must still be accessible after SQL injection attempt. "
            "Data integrity must be preserved."
        )


@allure.title("TC-API-SEC-02: SQL Injection — body field sanitized")
@pytest.mark.be
@pytest.mark.security
async def test_sql_injection_in_body_field_sanitized(client, admin_token, seed_data):
    """
    ตรวจสอบว่า SQL Injection ใน body field ไม่ทำลาย DB
    ระบบต้องเก็บค่าเป็น plain text หรือ return 422 — ไม่ 500
    """
    pattaya_branch = seed_data["branches"][0]
    mkt_source_type = seed_data["source_types"]["BPY_MKT"]
    sql_injection_name = "'; DROP TABLE customers; --"

    response = await post(client, "/customers",
                          token=admin_token,
                          json={
                              "first_name": sql_injection_name,
                              "last_name": "InjectionTest",
                              "branch_id": str(pattaya_branch.id),
                              "source_type_id": str(mkt_source_type.id),
                              "phone": "0812345678",
                              "status": "ACTIVE",
                          })

    with allure.step("Assert response is 201 (saved as plain text) or 422 (rejected) — never 500"):
        assert response.status_code in (201, 422), (
            f"Expected 201 or 422 for SQL injection in body field "
            f"but got {response.status_code}. "
            "SQL injection in body must be safely handled."
        )

    if response.status_code == 201:
        with allure.step("Assert SQL injection string stored as plain text"):
            customer_data = response.json()
            assert customer_data.get("first_name") == sql_injection_name, (
                "SQL injection string must be stored as literal text, not executed. "
                "Parameterized queries must prevent SQL execution."
            )

    with allure.step("Assert customers table still accessible"):
        verify_response = await get(client, "/customers",
                                    token=admin_token,
                                    expected_status=200)
        assert verify_response.status_code == 200, (
            "Customer table must remain accessible after SQL injection attempt."
        )


@allure.title("TC-API-SEC-03: Token cross-partner isolation — no data leakage")
@pytest.mark.be
@pytest.mark.security
async def test_token_cross_partner_data_isolation(client, seed_data):
    """
    ตรวจสอบว่า token ของ Partner A ใช้เรียก branch ของ Partner B ไม่ได้
    Cross-partner data isolation
    """
    from api.utils.auth import create_jwt_token

    partner_b_branch_id = seed_data.get("partner_b_branch_id")
    if not partner_b_branch_id:
        pytest.skip("Partner B not in seed data — skipping cross-partner isolation test")

    owner_token_str = create_jwt_token(
        user_id=str(seed_data["users"]["owner"].id),
        role="OWNER",
        branch_id=None,
        partner_id=str(seed_data["partner"].id),
        pin_verified=True,
    )

    response = await get(client, "/customers",
                         token=owner_token_str,
                         params={"branch_id": partner_b_branch_id})

    with allure.step("Assert 403 Forbidden — cannot access other partner's branch"):
        assert response.status_code == 403, (
            f"Expected 403 when accessing Partner B's branch with Partner A's token "
            f"but got {response.status_code}. "
            "Cross-partner data isolation must be enforced at API level."
        )
