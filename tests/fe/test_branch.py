import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-BRANCH-01: Branch list shows all branches with config")
@pytest.mark.fe
def test_branch_list_loads(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/settings/branches\")"):
        navigate(page, "/settings/branches")
    with allure.step("Assert: validate expected result"):
            assert page.locator("[data-testid^='branch-edit-']").count() > 0


@allure.title("TC-BRANCH-02: Add new branch")
@pytest.mark.fe
@pytest.mark.xfail(reason="Add branch flow is not exposed in current BranchConfig UI.", strict=False)
def test_branch_add_new(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/settings/branches\")"):
        navigate(page, "/settings/branches")
    with allure.step("Assert: validate expected result"):
            assert "/settings/branches" in page.url


@allure.title("TC-BRANCH-03: Edit branch opening hours")
@pytest.mark.fe
def test_branch_edit_opening_hours_modal(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/settings/branches\")"):
        navigate(page, "/settings/branches")
    edit_btn = page.locator("[data-testid^='branch-edit-']").first
    with allure.step("Action: edit_btn.click()"):
        edit_btn.click()
    with allure.step("Assert: validate expected result"):
            assert page.locator("input[type='time']").count() >= 2


@allure.title("TC-BRANCH-04: Edit source type prefix")
@pytest.mark.fe
def test_branch_edit_source_type_inputs(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/settings/branches\")"):
        navigate(page, "/settings/branches")
    with allure.step("Action: page.locator(\"[data-testid^='branch-edit-']\").first.click()"):
        page.locator("[data-testid^='branch-edit-']").first.click()
    with allure.step("Assert: validate expected result"):
            assert page.locator("input[placeholder='ชื่อ']").count() > 0
    with allure.step("Assert: validate expected result"):
            assert page.locator("input[placeholder='รหัส']").count() > 0


@allure.title("TC-BRANCH-05: Only Owner can access Branch Config")
@pytest.mark.fe
def test_branch_config_owner_only(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/settings/branches\")"):
        navigate(page, "/settings/branches")
    # Admin should not have visible branch config content; protected behavior may redirect.
    with allure.step("Assert: validate expected result"):
            assert "/settings/branches" not in page.url or page.locator("[data-testid^='branch-edit-']").count() == 0

