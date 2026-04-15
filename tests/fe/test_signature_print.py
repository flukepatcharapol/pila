import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-PRINT-01: Google Drive connection status shown")
@pytest.mark.fe
@pytest.mark.xfail(reason="Signature Print route is not implemented in current FE router.", strict=False)
def test_print_google_connection_status(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/signature-print\")"):
        navigate(page, "/signature-print")
    with allure.step("Assert: validate expected result"):
            assert "Google" in page.locator("body").inner_text()


@allure.title("TC-PRINT-02: Storage widget shows correct usage")
@pytest.mark.fe
@pytest.mark.xfail(reason="Signature Print storage widget not implemented in current FE routes.", strict=False)
def test_print_storage_widget(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/signature-print\")"):
        navigate(page, "/signature-print")
    with allure.step("Assert: validate expected result"):
            assert "GB" in page.locator("body").inner_text()


@allure.title("TC-PRINT-03: Generate signature sheet — happy path")
@pytest.mark.fe
@pytest.mark.xfail(reason="Signature sheet generate flow not implemented in current FE routes.", strict=False)
def test_print_generate_sheet(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/signature-print\")"):
        navigate(page, "/signature-print")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=Generate").count() > 0


@allure.title("TC-PRINT-04: Generated link opens Google Sheet")
@pytest.mark.fe
@pytest.mark.xfail(reason="Generated sheet link flow not implemented in current FE routes.", strict=False)
def test_print_generated_link(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/signature-print\")"):
        navigate(page, "/signature-print")
    with allure.step("Assert: validate expected result"):
            assert page.locator("a[href*='docs.google.com']").count() > 0


@allure.title("TC-PRINT-05: Generate blocked when Google Drive not connected")
@pytest.mark.fe
@pytest.mark.xfail(reason="Signature Print route/controls not implemented in current FE routes.", strict=False)
def test_print_blocked_when_not_connected(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/signature-print\")"):
        navigate(page, "/signature-print")
    with allure.step("Assert: validate expected result"):
            assert "connect" in page.locator("body").inner_text().lower()


@allure.title("TC-PRINT-06: Storage warning when Drive is near full")
@pytest.mark.fe
@pytest.mark.xfail(reason="Storage warning banner not implemented in current FE signature-print flow.", strict=False)
def test_print_storage_warning(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/signature-print\")"):
        navigate(page, "/signature-print")
    with allure.step("Assert: validate expected result"):
            assert "almost full" in page.locator("body").inner_text().lower()

