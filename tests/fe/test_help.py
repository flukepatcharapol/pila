import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-HELP-01: Help page loads correctly")
@pytest.mark.fe
def test_help_page_loads(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/help\")"):
        navigate(page, "/help")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=คู่มือการใช้งาน").count() > 0
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=ติดต่อ Support").count() > 0


@allure.title("TC-HELP-02: User manual shows role-specific content")
@pytest.mark.fe
def test_help_role_specific_manual(page, request):
    with allure.step("Action: login_as(page, role=\"trainer\", request=request)"):
        login_as(page, role="trainer", request=request)
    with allure.step("Action: navigate(page, \"/help\")"):
        navigate(page, "/help")
    page_text = page.locator("body").inner_text()
    with allure.step("Assert: validate expected result"):
            assert "การเบิกเซสชัน" in page_text
    with allure.step("Assert: validate expected result"):
            assert "การจัดการสิทธิ์ (Owner เท่านั้น)" not in page_text


@allure.title("TC-HELP-03: LINE Developer QR code visible")
@pytest.mark.fe
def test_help_developer_qr_section_visible(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/help\")"):
        navigate(page, "/help")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=LINE QR").count() > 0
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=ผู้พัฒนาระบบ").count() > 0


@allure.title("TC-HELP-04: LINE Branch group chat QR matches user's branch")
@pytest.mark.fe
@pytest.mark.xfail(reason="Branch-specific LINE QR rendering is not implemented in current FE Help page.", strict=False)
def test_help_branch_qr_matches_user_branch(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/help\")"):
        navigate(page, "/help")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=Kanchanaburi").count() > 0

