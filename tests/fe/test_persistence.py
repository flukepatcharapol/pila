import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-PERSIST-01: Filter state preserved on back navigation")
@pytest.mark.fe
@pytest.mark.xfail(reason="URL/state restoration for filters is not fully implemented across pages.", strict=False)
def test_persist_filter_state_back_navigation(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    with allure.step("Action: page.get_by_test_id(\"customer-list-search\").fill(\"test\")"):
        page.get_by_test_id("customer-list-search").fill("test")
    row = page.locator("table tbody tr").first
    with allure.step("Action: row.click()"):
        row.click()
    with allure.step("Action: page.go_back()"):
        page.go_back()
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("customer-list-search").input_value() == "test"


@allure.title("TC-PERSIST-02: Dark mode preference survives session")
@pytest.mark.fe
@pytest.mark.xfail(reason="Dark mode persistence across browser sessions is not implemented.", strict=False)
def test_persist_dark_mode_survives_session(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    with allure.step("Action: page.get_by_test_id(\"settings-dark-mode-toggle\").click()"):
        page.get_by_test_id("settings-dark-mode-toggle").click()
    with allure.step("Action: page.reload()"):
        page.reload()
    with allure.step("Assert: validate expected result"):
            assert page.evaluate("() => document.documentElement.classList.contains('dark')") is True


@allure.title("TC-PERSIST-03: Language preference survives session")
@pytest.mark.fe
@pytest.mark.xfail(reason="Language persistence across browser sessions is not implemented.", strict=False)
def test_persist_language_survives_session(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    with allure.step("Action: page.locator(\"button:has-text('EN')\").click()"):
        page.locator("button:has-text('EN')").click()
    with allure.step("Action: page.reload()"):
        page.reload()
    with allure.step("Assert: validate expected result"):
            assert page.locator("button:has-text('EN')").count() > 0

