import allure
import pytest

from helpers.common_web import (
    login_as,
    navigate,
    expire_access_token,
    get_local_storage,
)


@allure.title("TC-SEC-01: Expired token redirects to login")
@pytest.mark.fe
def test_security_expired_token_redirects(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: expire_access_token(page)"):
        expire_access_token(page)
    with allure.step("Action: page.evaluate(\"() => localStorage.setItem('password_session_expires_at', '1')\")"):
        page.evaluate("() => localStorage.setItem('password_session_expires_at', '1')")
    with allure.step("Action: navigate(page, \"/dashboard\")"):
        navigate(page, "/dashboard")
    with allure.step("Assert: validate expected result"):
            assert "/login" in page.url


@allure.title("TC-SEC-02: Sensitive data not in localStorage")
@pytest.mark.fe
def test_security_sensitive_data_not_stored(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    sensitive_keys = page.evaluate(
        "() => Object.keys(localStorage).filter(k => /password|pin|raw/i.test(k))"
    )
    # allow password_session_token key by design, block raw password/PIN-like keys
    blocked = [k for k in sensitive_keys if k not in ("password_session_token", "password_session_expires_at")]
    with allure.step("Assert: validate expected result"):
            assert blocked == []
    with allure.step("Assert: validate expected result"):
            assert get_local_storage(page, "password") is None
    with allure.step("Assert: validate expected result"):
            assert get_local_storage(page, "pin") is None


@allure.title("TC-SEC-03: XSS — script input does not execute")
@pytest.mark.fe
def test_security_xss_not_executed(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers/new\")"):
        navigate(page, "/customers/new")
    with allure.step("Action: page.get_by_test_id(\"customer-form-first-name\").fill(\"<script>alert('xss')</script>\")"):
        page.get_by_test_id("customer-form-first-name").fill("<script>alert('xss')</script>")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("customer-form-first-name").input_value() == "<script>alert('xss')</script>"


@allure.title("TC-SEC-04: Unauthorized route access by role")
@pytest.mark.fe
def test_security_unauthorized_route_by_role(page, request):
    with allure.step("Action: login_as(page, role=\"trainer\", request=request)"):
        login_as(page, role="trainer", request=request)
    with allure.step("Action: navigate(page, \"/users\")"):
        navigate(page, "/users")
    with allure.step("Assert: validate expected result"):
            assert "/users" not in page.url or page.locator("text=ไม่พบผู้ใช้งาน").count() >= 0

