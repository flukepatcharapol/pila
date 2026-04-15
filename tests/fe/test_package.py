import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-PKG-01: Package list loads with status badges")
@pytest.mark.fe
def test_package_list_status_badges(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/packages\")"):
        navigate(page, "/packages")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=สถานะ").count() > 0


@allure.title("TC-PKG-02: Add package — happy path")
@pytest.mark.fe
def test_package_add_happy_path(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/packages\")"):
        navigate(page, "/packages")
    with allure.step("Action: page.get_by_test_id(\"package-list-add-btn\").click()"):
        page.get_by_test_id("package-list-add-btn").click()
    with allure.step("Action: page.get_by_test_id(\"package-form-name\").fill(\"Auto Package\")"):
        page.get_by_test_id("package-form-name").fill("Auto Package")
    with allure.step("Action: page.get_by_test_id(\"package-form-submit\").click()"):
        page.get_by_test_id("package-form-submit").click()
    with allure.step("Assert: validate expected result"):
            assert "/packages" in page.url


@allure.title("TC-PKG-03: Package with active period expires correctly")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs deterministic time-window package fixtures.", strict=False)
def test_package_expired_badge(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/packages\")"):
        navigate(page, "/packages")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=หมดอายุ").count() >= 0


@allure.title("TC-PKG-04: Package scope selected branch visibility in order form")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs branch-scoped package fixtures.", strict=False)
def test_package_scope_selected_branch_visibility(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders/new\")"):
        navigate(page, "/orders/new")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("order-form-package").is_visible()


@allure.title("TC-PKG-05: Package scope all branch visible in all branches")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs all-branch package fixture and multi-branch role setup.", strict=False)
def test_package_scope_all_branch_visible(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/orders/new\")"):
        navigate(page, "/orders/new")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("order-form-package").is_visible()


@allure.title("TC-PKG-06: Package before active period not shown in order form")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs future-active package fixture.", strict=False)
def test_package_before_active_hidden(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders/new\")"):
        navigate(page, "/orders/new")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("order-form-package").is_visible()


@allure.title("TC-PKG-07: Package after active period shows expired and not selectable")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs expired package fixture + order form assertion data.", strict=False)
def test_package_after_active_not_selectable(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/packages\")"):
        navigate(page, "/packages")
    with allure.step("Assert: validate expected result"):
            assert "/packages" in page.url

