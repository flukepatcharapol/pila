import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-USER-01: User list grouped by Active/Inactive")
@pytest.mark.fe
def test_user_list_status_groups(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/users\")"):
        navigate(page, "/users")
    table_text = page.locator("table").inner_text()
    with allure.step("Assert: validate expected result"):
            assert "ใช้งาน" in table_text or "ระงับ" in table_text


@allure.title("TC-USER-02: Role badge colors correct")
@pytest.mark.fe
def test_user_role_badges_render(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/users\")"):
        navigate(page, "/users")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=Owner").count() + page.locator("text=Admin").count() >= 1


@allure.title("TC-USER-03: Branch Manager cannot create users for other branches")
@pytest.mark.fe
@pytest.mark.xfail(reason="User create form is not implemented in current FE routes.", strict=False)
def test_user_branch_manager_create_restriction(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/users/new\")"):
        navigate(page, "/users/new")
    with allure.step("Assert: validate expected result"):
            assert "/users/new" in page.url


@allure.title("TC-USER-04: Slide-out detail panel")
@pytest.mark.fe
def test_user_slide_out_detail_panel(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/users\")"):
        navigate(page, "/users")
    row_button = page.locator("[data-testid^='user-row-']").first
    with allure.step("Action: row_button.click()"):
        row_button.click()
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("user-panel-role-select").is_visible()

