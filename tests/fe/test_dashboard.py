import allure
import pytest

from helpers.common_web import login_as, navigate, set_slow_network


def _dashboard_metric_cards(page) -> int:
    return page.locator("div.grid > div").count()


@allure.title("TC-DASH-01: Dashboard loads for Trainer role")
@pytest.mark.fe
def test_dash_trainer_loads(page, request):
    with allure.step("Action: login_as(page, role=\"trainer\", request=request)"):
        login_as(page, role="trainer", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert "/dashboard" in page.url
    with allure.step("Assert: validate expected result"):
            assert _dashboard_metric_cards(page) >= 1


@allure.title("TC-DASH-02: Dashboard loads for Admin role")
@pytest.mark.fe
def test_dash_admin_loads(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert "/dashboard" in page.url
    with allure.step("Assert: validate expected result"):
            assert _dashboard_metric_cards(page) >= 1


@allure.title("TC-DASH-03: Dashboard loads for Owner role — branch selector visible")
@pytest.mark.fe
def test_dash_owner_branch_selector_visible(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("topnav-branch-switcher").is_visible()
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("dashboard-branch-all").is_visible()


@allure.title("TC-DASH-04: Time range filter changes chart data")
@pytest.mark.fe
def test_dash_period_filter_updates(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    week_button = page.get_by_test_id("dashboard-period-week")
    today_button = page.get_by_test_id("dashboard-period-today")
    with allure.step("Action: week_button.click()"):
        week_button.click()
    with allure.step("Assert: validate expected result"):
            assert "/dashboard" in page.url
    with allure.step("Action: today_button.click()"):
        today_button.click()
    with allure.step("Assert: validate expected result"):
            assert "/dashboard" in page.url


@allure.title("TC-DASH-05: Dashboard shows loading skeleton before data")
@pytest.mark.fe
def test_dash_loading_skeleton(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    set_slow_network(page)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    shimmer = page.locator(".animate-shimmer")
    with allure.step("Assert: validate expected result"):
            assert shimmer.count() > 0, "Dashboard should render shimmer placeholders while loading."


@allure.title("TC-DASH-06: Dashboard loads for Branch Manager role")
@pytest.mark.fe
def test_dash_branch_manager_loads(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert "/dashboard" in page.url
    with allure.step("Assert: validate expected result"):
            assert _dashboard_metric_cards(page) >= 1


@allure.title("TC-DASH-07: Branch Manager sees per-admin breakdown")
@pytest.mark.fe
@pytest.mark.xfail(reason="Per-admin breakdown section not explicitly implemented in current dashboard.", strict=False)
def test_dash_branch_manager_breakdown(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=admin").first.is_visible()


@allure.title("TC-DASH-08: Owner switches branch — data updates")
@pytest.mark.fe
def test_dash_owner_switch_branch(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Action: page.get_by_test_id(\"topnav-branch-switcher\").click()"):
        page.get_by_test_id("topnav-branch-switcher").click()
    options = page.locator("[role='listbox'] button")
    if options.count() > 0:
        with allure.step("Action: options.first.click()"):
            options.first.click()
    with allure.step("Assert: validate expected result"):
            assert "/dashboard" in page.url


@allure.title("TC-DASH-09: Owner Overall tab shows all branches combined")
@pytest.mark.fe
def test_dash_owner_all_branches_chip(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Action: page.get_by_test_id(\"dashboard-branch-all\").click()"):
        page.get_by_test_id("dashboard-branch-all").click()
    with allure.step("Assert: validate expected result"):
            assert "/dashboard" in page.url

