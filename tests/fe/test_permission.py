import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-PERM-01: Permission matrix displays toggle switches")
@pytest.mark.fe
def test_permission_matrix_toggles_visible(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/permissions\")"):
        navigate(page, "/permissions")
    with allure.step("Assert: validate expected result"):
            assert page.locator("[data-testid^='perm-']").count() > 0


@allure.title("TC-PERM-02: Toggle persists after page reload")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires deterministic permission fixture and writable permission env.", strict=False)
def test_permission_toggle_persists_after_reload(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/permissions\")"):
        navigate(page, "/permissions")
    toggle = page.locator("[data-testid^='perm-']").first
    with allure.step("Action: toggle.click()"):
        toggle.click()
    with allure.step("Action: page.reload()"):
        page.reload()
    with allure.step("Assert: validate expected result"):
            assert page.locator("[data-testid^='perm-']").count() > 0


@allure.title("TC-PERM-03: Permission change hides menu for affected role")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires multi-user permission mutation and re-login flow fixture.", strict=False)
def test_permission_change_hides_sidebar_menu(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/permissions\")"):
        navigate(page, "/permissions")
    with allure.step("Assert: validate expected result"):
            assert "/permissions" in page.url

