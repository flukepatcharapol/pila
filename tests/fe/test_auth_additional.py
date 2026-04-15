import allure
import pytest

from helpers.common_web import login_as, navigate, wait_for_url, fill, click


@allure.title("TC-AUTH-07: Forgot PIN — OTP flow")
@pytest.mark.fe
@pytest.mark.xfail(reason="Forgot PIN OTP route/flow is not implemented in current FE routes.", strict=False)
def test_auth_forgot_pin_otp_flow(page, request):
    with allure.step("Action: navigate(page, \"/pin\")"):
        navigate(page, "/pin")
    with allure.step("Action: page.get_by_test_id(\"back-to-login\").click()"):
        page.get_by_test_id("back-to-login").click()
    with allure.step("Assert: validate expected result"):
            assert "/pin/reset" in page.url


@allure.title("TC-AUTH-09: Login returns temporary token indicator (not full access)")
@pytest.mark.fe
def test_auth_temp_token_cannot_access_protected(page, request):
    with allure.step("Action: navigate(page, \"/login\")"):
        navigate(page, "/login")
    with allure.step("Action: fill(email-input)"):
        fill(page, "email-input", "//input[@id='email']", "admin@test.com", request)
    with allure.step("Action: fill(password-input)"):
        fill(page, "password-input", "//input[@id='password']", "test_pass", request)
    with allure.step("Action: click(login-submit)"):
        click(page, "login-submit", "//button[@type='submit']", request)
    with allure.step("Action: wait_for_url(page, \"**/pin\")"):
        wait_for_url(page, "**/pin")
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    with allure.step("Assert: validate expected result"):
            assert "/pin" in page.url


@allure.title("TC-AUTH-10: PIN verify completes authentication (JWT issued)")
@pytest.mark.fe
def test_auth_pin_verify_grants_protected_access(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    with allure.step("Assert: validate expected result"):
            assert "/customers" in page.url


@allure.title("TC-AUTH-11: Forgot password — request reset email")
@pytest.mark.fe
@pytest.mark.xfail(reason="Forgot-password route is not implemented in current FE routes.", strict=False)
def test_auth_forgot_password_request(page, request):
    with allure.step("Action: navigate(page, \"/forgot-password\")"):
        navigate(page, "/forgot-password")
    with allure.step("Assert: validate expected result"):
            assert "/forgot-password" in page.url


@allure.title("TC-AUTH-12: Forgot password — reset with valid token")
@pytest.mark.fe
@pytest.mark.xfail(reason="Reset-password route is not implemented in current FE routes.", strict=False)
def test_auth_reset_password_with_token(page, request):
    with allure.step("Action: navigate(page, \"/reset-password?token=valid_token\")"):
        navigate(page, "/reset-password?token=valid_token")
    with allure.step("Assert: validate expected result"):
            assert "/reset-password" in page.url


@allure.title("TC-AUTH-13: Change password while logged in")
@pytest.mark.fe
@pytest.mark.xfail(reason="Change password UI is not implemented in current settings page.", strict=False)
def test_auth_change_password_logged_in(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    with allure.step("Assert: validate expected result"):
            assert "Change Password" in page.locator("body").inner_text()

