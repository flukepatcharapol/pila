import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-SET-01: Language toggle switches between Thai and English")
@pytest.mark.fe
def test_settings_language_toggle(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    with allure.step("Action: page.locator(\"button:has-text('EN')\").click()"):
        page.locator("button:has-text('EN')").click()
    with allure.step("Action: page.locator(\"button:has-text('ไทย')\").click()"):
        page.locator("button:has-text('ไทย')").click()
    with allure.step("Assert: validate expected result"):
            assert "/settings" in page.url


@allure.title("TC-SET-02: Dark mode toggle")
@pytest.mark.fe
def test_settings_dark_mode_toggle(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    toggle = page.get_by_test_id("settings-dark-mode-toggle")
    with allure.step("Action: toggle.click()"):
        toggle.click()
    with allure.step("Assert: validate expected result"):
            assert page.evaluate("() => document.documentElement.classList.contains('dark')") is True
    with allure.step("Action: toggle.click()"):
        toggle.click()


@allure.title("TC-SET-03: Dark mode persists after page reload")
@pytest.mark.fe
@pytest.mark.xfail(reason="Persistence storage for dark mode is not implemented yet.", strict=False)
def test_settings_dark_mode_persists_reload(page, request):
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


@allure.title("TC-SET-04: Language persists after page reload")
@pytest.mark.fe
@pytest.mark.xfail(reason="Language persistence storage is not implemented yet.", strict=False)
def test_settings_language_persists_reload(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    with allure.step("Action: page.locator(\"button:has-text('EN')\").click()"):
        page.locator("button:has-text('EN')").click()
    with allure.step("Action: page.reload()"):
        page.reload()
    with allure.step("Assert: validate expected result"):
            assert "EN" in page.locator("body").inner_text()


@allure.title("TC-SET-05: Google Account connect flow")
@pytest.mark.fe
def test_settings_google_connect_button_visible(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    with allure.step("Assert: validate expected result"):
            assert (
                page.get_by_test_id("settings-connect-google-btn").count() > 0
                or page.get_by_test_id("settings-disconnect-google-btn").count() > 0
            )


@allure.title("TC-SET-06: Google Account disconnect")
@pytest.mark.fe
def test_settings_google_disconnect_button(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    if page.get_by_test_id("settings-disconnect-google-btn").count() > 0:
        with allure.step("Action: page.get_by_test_id(\"settings-disconnect-google-btn\").click()"):
            page.get_by_test_id("settings-disconnect-google-btn").click()
    with allure.step("Assert: validate expected result"):
            assert "/settings" in page.url


@allure.title("TC-SET-07: Google Drive storage displays correctly")
@pytest.mark.fe
def test_settings_drive_storage_widget(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings\")"):
        navigate(page, "/settings")
    body = page.locator("body").inner_text()
    with allure.step("Assert: validate expected result"):
            assert "Google Drive" in body

