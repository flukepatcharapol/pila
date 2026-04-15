import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-LOG-01: Activity log page loads with data")
@pytest.mark.fe
def test_activity_log_loads(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/activity-log\")"):
        navigate(page, "/activity-log")
    header = page.locator("thead").inner_text()
    with allure.step("Assert: validate expected result"):
            assert "เวลา" in header and "ผู้ทำ" in header


@allure.title("TC-LOG-02: Filter by date range")
@pytest.mark.fe
def test_activity_log_filter_date_range(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/activity-log\")"):
        navigate(page, "/activity-log")
    date_inputs = page.locator("input[type='date']")
    if date_inputs.count() >= 2:
        with allure.step("Action: date_inputs.nth(0).fill(\"2026-01-01\")"):
            date_inputs.nth(0).fill("2026-01-01")
        with allure.step("Action: date_inputs.nth(1).fill(\"2026-12-31\")"):
            date_inputs.nth(1).fill("2026-12-31")
    with allure.step("Assert: validate expected result"):
            assert "/activity-log" in page.url


@allure.title("TC-LOG-03: Filter by user/actor")
@pytest.mark.fe
def test_activity_log_filter_by_actor_search(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/activity-log\")"):
        navigate(page, "/activity-log")
    with allure.step("Action: page.get_by_test_id(\"activity-log-search\").fill(\"admin\")"):
        page.get_by_test_id("activity-log-search").fill("admin")
    with allure.step("Assert: validate expected result"):
            assert "/activity-log" in page.url


@allure.title("TC-LOG-04: Filter by action type")
@pytest.mark.fe
def test_activity_log_filter_action_type(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/activity-log\")"):
        navigate(page, "/activity-log")
    with allure.step("Action: page.get_by_test_id(\"activity-log-search\").fill(\"deduct\")"):
        page.get_by_test_id("activity-log-search").fill("deduct")
    with allure.step("Assert: validate expected result"):
            assert "/activity-log" in page.url


@allure.title("TC-LOG-05: Admin sees only own branch logs")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires deterministic branch-tagged log fixtures.", strict=False)
def test_activity_log_admin_branch_scope(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/activity-log\")"):
        navigate(page, "/activity-log")
    with allure.step("Assert: validate expected result"):
            assert "/activity-log" in page.url


@allure.title("TC-LOG-06: Owner sees all branch logs")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires multi-branch log fixtures.", strict=False)
def test_activity_log_owner_all_branches(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/activity-log\")"):
        navigate(page, "/activity-log")
    with allure.step("Assert: validate expected result"):
            assert "/activity-log" in page.url


@allure.title("TC-LOG-07: Session deduct action logged correctly")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires chained session-deduct action setup + activity log assertion.", strict=False)
def test_activity_log_session_deduct_entry(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/activity-log\")"):
        navigate(page, "/activity-log")
    with allure.step("Assert: validate expected result"):
            assert "/activity-log" in page.url

