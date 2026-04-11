# tests/be/test_package_api.py
#
# BE tests สำหรับ Package API
# TC-API-PKG-01 ถึง TC-API-PKG-07

import pytest
import allure
from helpers.common_api import (
    get, post, delete,
    assert_forbidden, assert_conflict,
)


# ─── GET /packages ────────────────────────────────────────────────────────────────

@allure.title("TC-API-PKG-01: GET /packages — returns list with computed status")
@pytest.mark.be
async def test_package_list_includes_computed_status(client, admin_token, create_package):
    """ตรวจสอบว่า GET /packages คืน list พร้อม computed status (active/inactive/expired)"""
    create_package(is_active=True)

    response = await get(client, "/packages", token=admin_token, expected_status=200)

    with allure.step("Assert each package has computed status"):
        package_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        assert len(package_list) >= 1, "At least one package must be returned."
        for package_data in package_list:
            assert "status" in package_data, (
                f"Package {package_data.get('id')} must have computed 'status' field. "
                "Status should be: active, inactive, or expired."
            )


@allure.title("TC-API-PKG-03: GET /packages?active_only=true — only active packages returned")
@pytest.mark.be
async def test_package_list_active_only_filter(client, admin_token,
                                                create_package, expired_package):
    """ตรวจสอบว่า ?active_only=true ไม่มี expired หรือ inactive package"""
    create_package(is_active=True)   # active
    expired_package                   # already created expired package

    response = await get(client, "/packages",
                         token=admin_token,
                         params={"active_only": "true"},
                         expected_status=200)

    with allure.step("Assert no expired or inactive packages in response"):
        package_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        for package_data in package_list:
            package_status = package_data.get("status", "").lower()
            assert package_status not in ("expired", "inactive"), (
                f"Package {package_data.get('id')} has status='{package_status}' "
                "but should not appear when active_only=true."
            )


@allure.title("TC-API-PKG-04: Package status computed as 'expired' when active_until = yesterday")
@pytest.mark.be
async def test_package_expired_status_computed_correctly(client, admin_token,
                                                          expired_package):
    """ตรวจสอบว่า package ที่ active_until = เมื่อวาน มี computed status = 'expired'"""
    response = await get(client, "/packages", token=admin_token, expected_status=200)

    with allure.step("Assert expired package has status='expired'"):
        package_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        expired_package_entries = [
            pkg for pkg in package_list if pkg.get("id") == expired_package
        ]
        assert len(expired_package_entries) >= 1, (
            "Expired package must appear in full package list (not filtered)."
        )
        for package_data in expired_package_entries:
            assert package_data.get("status", "").lower() == "expired", (
                f"Package with active_until=yesterday must have status='expired' "
                f"but got '{package_data.get('status')}'."
            )


@allure.title("TC-API-PKG-07: GET /packages?active_only=true — future package excluded")
@pytest.mark.be
async def test_future_package_excluded_from_active_only(client, admin_token, future_package):
    """ตรวจสอบว่า package ที่ active_from = พรุ่งนี้ ไม่ถูก return เมื่อ active_only=true"""
    response = await get(client, "/packages",
                         token=admin_token,
                         params={"active_only": "true"},
                         expected_status=200)

    with allure.step("Assert future package not in active_only results"):
        package_list = response.json() if isinstance(response.json(), list) else response.json().get("items", [])
        returned_ids = {pkg.get("id") for pkg in package_list}
        assert future_package not in returned_ids, (
            f"Package with active_from=tomorrow must NOT appear in active_only results. "
            "Package is not yet active."
        )


# ─── POST /packages ───────────────────────────────────────────────────────────────

@allure.title("TC-API-PKG-02: POST /packages — create valid package")
@pytest.mark.be
async def test_create_package_valid(client, owner_token, seed_data):
    """ตรวจสอบว่าสร้าง package ด้วย payload ถูกต้อง → 201 Created"""
    from datetime import date, timedelta

    package_payload = {
        "name": "Test Sale Package",
        "hours": 10,
        "type": "SALE",
        "price": 5000.0,
        "branch_scope": "ALL",
        "active_from": str(date.today()),
        "active_until": str(date.today() + timedelta(days=365)),
    }

    response = await post(client, "/packages",
                          token=owner_token,
                          json=package_payload,
                          expected_status=201)

    with allure.step("Assert package created with correct fields"):
        package_data = response.json()
        assert "id" in package_data, "Package response must contain 'id'."
        assert package_data.get("hours") == 10, (
            f"Expected hours=10 but got {package_data.get('hours')}."
        )


# ─── DELETE /packages ─────────────────────────────────────────────────────────────

@allure.title("TC-API-PKG-05: DELETE /packages — success when no active orders")
@pytest.mark.be
async def test_delete_package_with_no_orders(client, owner_token, create_package):
    """ตรวจสอบว่าลบ package ที่ไม่มี order → 204 No Content"""
    package_id = create_package()

    await delete(client, f"/packages/{package_id}",
                 token=owner_token, expected_status=204)


@allure.title("TC-API-PKG-06: DELETE /packages — fail if package used in active orders")
@pytest.mark.be
async def test_delete_package_with_active_orders_rejected(client, owner_token,
                                                           create_package, create_order):
    """ตรวจสอบว่าลบ package ที่มี order อ้างอิงอยู่ → 409 Conflict"""
    package_id = create_package()
    create_order(package_id=package_id)

    response = await delete(client, f"/packages/{package_id}",
                            token=owner_token)

    assert_conflict(response, expected_detail="referenced by existing orders")
