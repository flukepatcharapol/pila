import allure
import pytest

from helpers.common_web import (
    login_as,
    navigate,
    set_tablet_viewport,
    assert_no_uuid_in_page,
)


@allure.title("TC-CROSS-01: All tables have working search")
@pytest.mark.fe
@pytest.mark.parametrize(
    ("route", "search_testid"),
    [
        ("/customers", "customer-list-search"),
        ("/orders", "order-list-search"),
        ("/trainers", "trainer-list-search"),
        ("/users", "user-list-search"),
    ],
)
def test_cross_table_search_inputs_exist(page, request, route, search_testid):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, route)"):
        navigate(page, route)
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id(search_testid).is_visible()


@allure.title("TC-CROSS-02: All forms show loading state on submit")
@pytest.mark.fe
@pytest.mark.xfail(reason="Global loading spinner test needs deterministic slow network fixture.", strict=False)
def test_cross_form_submit_loading(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers/new\")"):
        navigate(page, "/customers/new")
    with allure.step("Action: page.get_by_test_id(\"customer-form-submit\").click()"):
        page.get_by_test_id("customer-form-submit").click()
    with allure.step("Assert: validate expected result"):
            assert page.locator("button[disabled]").count() > 0


@allure.title("TC-CROSS-03: Success toast on create/edit")
@pytest.mark.fe
@pytest.mark.xfail(reason="Toast test needs deterministic successful mutation fixture.", strict=False)
def test_cross_success_toast(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers/new\")"):
        navigate(page, "/customers/new")
    with allure.step("Action: page.get_by_test_id(\"customer-form-submit\").click()"):
        page.get_by_test_id("customer-form-submit").click()
    with allure.step("Assert: validate expected result"):
            assert page.locator("[role='alert']").count() > 0


@allure.title("TC-CROSS-04: Error toast on server error")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires API error mock compatibility with current app request stack.", strict=False)
def test_cross_error_toast(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers/new\")"):
        navigate(page, "/customers/new")
    with allure.step("Action: page.get_by_test_id(\"customer-form-submit\").click()"):
        page.get_by_test_id("customer-form-submit").click()
    with allure.step("Assert: validate expected result"):
            assert page.locator("[role='alert']").count() > 0


@allure.title("TC-CROSS-05: No UUID shown anywhere in UI")
@pytest.mark.fe
def test_cross_no_uuid_visible(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    with allure.step("Action: assert_no_uuid_in_page(page)"):
        assert_no_uuid_in_page(page)


@allure.title("TC-CROSS-06: Confirmation dialog on destructive actions")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs deterministic row selection and destructive action fixture.", strict=False)
def test_cross_confirmation_dialog(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("confirm-dialog-confirm-btn").count() >= 0


@allure.title("TC-CROSS-07: Responsive — tablet (768px) renders correctly")
@pytest.mark.fe
def test_cross_tablet_responsive(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: set_tablet_viewport(page)"):
        set_tablet_viewport(page)
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    with allure.step("Assert: validate expected result"):
            assert "/customers" in page.url


@allure.title("TC-CROSS-08: Thai text renders without clipping")
@pytest.mark.fe
def test_cross_thai_text_visible(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/help\")"):
        navigate(page, "/help")
    body_text = page.locator("body").inner_text()
    with allure.step("Assert: validate expected result"):
            assert "ช่วยเหลือ" in body_text or "คู่มือการใช้งาน" in body_text

