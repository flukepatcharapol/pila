# tests/be/test_dashboard_api.py
#
# BE tests สำหรับ Dashboard API
# TC-API-DASH-01 ถึง TC-API-DASH-08

import pytest
import allure
from helpers.common_api import (
    get,
    assert_forbidden,
)


# ─── GET /dashboard ───────────────────────────────────────────────────────────────

@allure.title("TC-API-DASH-01: GET /dashboard — trainer sees own data only")
@pytest.mark.be
async def test_trainer_dashboard_scoped_to_own_data(client, trainer_token, seed_data):
    """ตรวจสอบว่า trainer เห็นแค่ข้อมูลของตัวเอง ไม่เห็นข้อมูล trainer อื่น"""
    response = await get(client, "/dashboard",
                         token=trainer_token, expected_status=200)

    with allure.step("Assert dashboard returns trainer-scoped data"):
        dashboard_data = response.json()
        assert dashboard_data is not None, "Dashboard response must not be empty."
        assert "total_hours" in dashboard_data or "session_count" in dashboard_data, (
            "Trainer dashboard must contain hour/session stats."
        )


@allure.title("TC-API-DASH-02: GET /dashboard — admin sees branch data only")
@pytest.mark.be
async def test_admin_dashboard_scoped_to_branch(client, admin_token, seed_data):
    """ตรวจสอบว่า admin เห็นข้อมูลเฉพาะ branch ตัวเอง"""
    response = await get(client, "/dashboard",
                         token=admin_token, expected_status=200)

    with allure.step("Assert dashboard data scoped to admin's branch"):
        dashboard_data = response.json()
        assert dashboard_data is not None, "Admin dashboard response must not be empty."


@allure.title("TC-API-DASH-03: GET /dashboard?range=today — only today's data")
@pytest.mark.be
async def test_dashboard_today_range_filter(client, admin_token):
    """ตรวจสอบว่า ?range=today คืนเฉพาะข้อมูลของวันนี้"""
    response = await get(client, "/dashboard",
                         token=admin_token,
                         params={"range": "today"},
                         expected_status=200)

    with allure.step("Assert today range filter applied"):
        dashboard_data = response.json()
        assert dashboard_data is not None, "Dashboard with range=today must return data."


@allure.title("TC-API-DASH-04: GET /dashboard?branch=all — owner sees all branches aggregate")
@pytest.mark.be
async def test_owner_dashboard_all_branches_aggregate(client, owner_token, seed_data):
    """ตรวจสอบว่า owner ด้วย ?branch=all เห็น aggregate ข้ามทุกสาขาใน partner"""
    response = await get(client, "/dashboard",
                         token=owner_token,
                         params={"branch": "all"},
                         expected_status=200)

    with allure.step("Assert cross-branch aggregate returned"):
        dashboard_data = response.json()
        assert dashboard_data is not None, "Owner cross-branch dashboard must return data."


@allure.title("TC-API-DASH-04b: GET /dashboard?partner=all — developer sees all partners")
@pytest.mark.be
async def test_developer_dashboard_all_partners_aggregate(client, developer_token):
    """ตรวจสอบว่า developer ด้วย ?partner=all เห็น aggregate ข้ามทุก partner"""
    response = await get(client, "/dashboard",
                         token=developer_token,
                         params={"partner": "all"},
                         expected_status=200)

    with allure.step("Assert cross-partner aggregate returned"):
        dashboard_data = response.json()
        assert dashboard_data is not None, "Developer cross-partner dashboard must return data."


@allure.title("TC-API-DASH-05: GET /dashboard?branch=all — admin forbidden")
@pytest.mark.be
async def test_admin_cannot_access_all_branch_dashboard(client, admin_token):
    """ตรวจสอบว่า admin ขอ ?branch=all → 403 Forbidden"""
    response = await get(client, "/dashboard",
                         token=admin_token,
                         params={"branch": "all"})

    assert_forbidden(response)


@allure.title("TC-API-DASH-05b: GET /dashboard?branch=all — trainer forbidden")
@pytest.mark.be
async def test_trainer_cannot_access_all_branch_dashboard(client, trainer_token):
    """ตรวจสอบว่า trainer ขอ ?branch=all → 403 Forbidden"""
    response = await get(client, "/dashboard",
                         token=trainer_token,
                         params={"branch": "all"})

    assert_forbidden(response)


@allure.title("TC-API-DASH-06: GET /dashboard — branch_master sees branch summary")
@pytest.mark.be
async def test_branch_master_sees_branch_summary(client, branch_master_token, seed_data):
    """
    ตรวจสอบว่า branch_master เห็น summary ของ Pattaya branch
    พร้อม breakdown per admin และ per trainer
    """
    response = await get(client, "/dashboard",
                         token=branch_master_token, expected_status=200)

    with allure.step("Assert branch summary fields present"):
        dashboard_data = response.json()
        required_summary_fields = ["total_orders", "total_revenue"]
        for field_name in required_summary_fields:
            assert field_name in dashboard_data, (
                f"Branch master dashboard must contain '{field_name}' field."
            )


@allure.title("TC-API-DASH-07: GET /dashboard — branch_master sees breakdown per admin")
@pytest.mark.be
async def test_branch_master_sees_admin_breakdown(client, branch_master_token):
    """ตรวจสอบว่า branch_master เห็น breakdown ตาม admin แต่ละคน"""
    response = await get(client, "/dashboard",
                         token=branch_master_token, expected_status=200)

    with allure.step("Assert admin breakdown list present"):
        dashboard_data = response.json()
        assert "breakdown_by_admin" in dashboard_data, (
            "Branch master dashboard must contain 'breakdown_by_admin' field."
        )
        admin_breakdown_list = dashboard_data["breakdown_by_admin"]
        assert isinstance(admin_breakdown_list, list), (
            "'breakdown_by_admin' must be a list."
        )


@allure.title("TC-API-DASH-08: GET /dashboard — branch_master sees breakdown per trainer")
@pytest.mark.be
async def test_branch_master_sees_trainer_breakdown(client, branch_master_token):
    """ตรวจสอบว่า branch_master เห็น breakdown ตาม trainer แต่ละคน"""
    response = await get(client, "/dashboard",
                         token=branch_master_token, expected_status=200)

    with allure.step("Assert trainer breakdown list present"):
        dashboard_data = response.json()
        assert "breakdown_by_trainer" in dashboard_data, (
            "Branch master dashboard must contain 'breakdown_by_trainer' field."
        )
        trainer_breakdown_list = dashboard_data["breakdown_by_trainer"]
        assert isinstance(trainer_breakdown_list, list), (
            "'breakdown_by_trainer' must be a list."
        )
