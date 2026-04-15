import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-ERR-01: JS error boundary shows fallback UI")
@pytest.mark.fe
@pytest.mark.xfail(reason="No global FE error boundary route/trigger is currently exposed.", strict=False)
def test_error_boundary_fallback_ui(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=Something went wrong").count() > 0


@allure.title("TC-ERR-02: Network timeout shows retry option")
@pytest.mark.fe
@pytest.mark.xfail(reason="Retry button UX is not consistently implemented across list pages.", strict=False)
def test_error_network_timeout_retry(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=Retry").count() > 0


@allure.title("TC-ERR-03: 401 Unauthorized redirects to login")
@pytest.mark.fe
def test_error_401_redirects_login(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    page.context.clear_cookies()
    with allure.step("Action: page.evaluate(\"() => { localStorage.removeItem('access_token'); localStorage.setItem('..."):
        page.evaluate("() => { localStorage.removeItem('access_token'); localStorage.setItem('password_session_expires_at', '1'); }")
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert "/login" in page.url


@allure.title("TC-ERR-04: 403 Forbidden shows access denied page")
@pytest.mark.fe
@pytest.mark.xfail(reason="Dedicated /403 page is not currently routed in FE.", strict=False)
def test_error_403_access_denied_page(page, request):
    with allure.step("Action: login_as(page, role=\"trainer\", request=request)"):
        login_as(page, role="trainer", request=request)
    with allure.step("Action: navigate(page, \"/settings/branches\")"):
        navigate(page, "/settings/branches")
    with allure.step("Assert: validate expected result"):
            assert "/403" in page.url or page.locator("text=ไม่มีสิทธิ์เข้าถึง").count() > 0


@allure.title("TC-ERR-05: 404 Not Found shows 404 page")
@pytest.mark.fe
@pytest.mark.xfail(reason="App currently redirects unknown routes to dashboard/login rather than custom 404 page.", strict=False)
def test_error_404_page(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/nonexistent-route\")"):
        navigate(page, "/nonexistent-route")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=404").count() > 0

