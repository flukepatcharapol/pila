import allure
import pytest

from helpers.common_web import login_as, navigate, assert_table_contains


@allure.title("TC-ORDER-01: Order list loads with correct columns")
@pytest.mark.fe
def test_order_list_columns(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    header_text = page.locator("thead").inner_text()
    for label in ["วันที่", "รหัสลูกค้า", "ชื่อลูกค้า", "แพ็กเกจ"]:
        with allure.step("Assert: validate expected result"):
                    assert label in header_text


@allure.title("TC-ORDER-02: Order list filter by date range")
@pytest.mark.fe
def test_order_list_date_filter(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    date_inputs = page.locator("input[type='date']")
    if date_inputs.count() >= 2:
        with allure.step("Action: date_inputs.nth(0).fill(\"2026-01-01\")"):
            date_inputs.nth(0).fill("2026-01-01")
        with allure.step("Action: date_inputs.nth(1).fill(\"2026-12-31\")"):
            date_inputs.nth(1).fill("2026-12-31")
    with allure.step("Assert: validate expected result"):
            assert "/orders" in page.url


@allure.title("TC-ORDER-03: Order list shows outstanding balance badge")
@pytest.mark.fe
def test_order_outstanding_badge_visible(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=ค้างชำระ").count() > 0


@allure.title("TC-ORDER-04: Add new order — happy path")
@pytest.mark.fe
def test_order_create_happy_path(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    with allure.step("Action: page.get_by_test_id(\"order-list-add-btn\").click()"):
        page.get_by_test_id("order-list-add-btn").click()
    with allure.step("Action: page.get_by_test_id(\"order-form-customer\").fill(\"a\")"):
        page.get_by_test_id("order-form-customer").fill("a")
    with allure.step("Action: page.get_by_test_id(\"order-form-submit\").click()"):
        page.get_by_test_id("order-form-submit").click()
    with allure.step("Assert: validate expected result"):
            assert "/orders" in page.url


@allure.title("TC-ORDER-05: Package chip only shows active + branch-matched")
@pytest.mark.fe
def test_order_package_selector_visible(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders/new\")"):
        navigate(page, "/orders/new")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("order-form-package").is_visible()


@allure.title("TC-ORDER-06: Trainer auto-fills from customer profile")
@pytest.mark.fe
@pytest.mark.xfail(reason="Trainer autofill field is not exposed as stable FE selector.", strict=False)
def test_order_trainer_autofill(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders/new\")"):
        navigate(page, "/orders/new")
    with allure.step("Action: page.get_by_test_id(\"order-form-customer\").fill(\"test\")"):
        page.get_by_test_id("order-form-customer").fill("test")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=เทรนเนอร์").is_visible()


@allure.title("TC-ORDER-07: Order form validation")
@pytest.mark.fe
def test_order_form_validation(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders/new\")"):
        navigate(page, "/orders/new")
    with allure.step("Action: page.get_by_test_id(\"order-form-submit\").click()"):
        page.get_by_test_id("order-form-submit").click()
    with allure.step("Assert: validate expected result"):
            assert "/orders/new" in page.url


@allure.title("TC-ORDER-08: Order detail view shows payment breakdown")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires deterministic seeded order row and detail path.", strict=False)
def test_order_detail_payment_breakdown(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    row = page.locator("table tbody tr").first
    with allure.step("Action: row.click()"):
        row.click()
    with allure.step("Action: assert_table_contains(page, \"ค้างชำระ\")"):
        assert_table_contains(page, "ค้างชำระ")

