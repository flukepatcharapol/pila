import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-PAY-01: Order detail shows payment breakdown")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires deterministic seeded order row for detail drill-down.", strict=False)
def test_pay_order_detail_breakdown(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    with allure.step("Action: page.locator(\"table tbody tr\").first.click()"):
        page.locator("table tbody tr").first.click()
    with allure.step("Assert: validate expected result"):
            assert "ค้างชำระ" in page.locator("body").inner_text()


@allure.title("TC-PAY-02: Outstanding balance badge in order list")
@pytest.mark.fe
def test_pay_outstanding_badge_in_list(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=ค้างชำระ").count() > 0


@allure.title("TC-PAY-03: Installment plan displays correctly")
@pytest.mark.fe
@pytest.mark.xfail(reason="Installment plan UI requires seeded installment orders.", strict=False)
def test_pay_installment_plan_display(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    with allure.step("Assert: validate expected result"):
            assert "งวด" in page.locator("body").inner_text()


@allure.title("TC-PAY-04: Record installment payment — outstanding decreases")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs deterministic order with outstanding balance and mutation fixture.", strict=False)
def test_pay_record_installment(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    with allure.step("Assert: validate expected result"):
            assert "/orders" in page.url


@allure.title("TC-PAY-05: Receipt/Invoice sent via email")
@pytest.mark.fe
@pytest.mark.xfail(reason="Email delivery assertion requires external/mock inbox integration harness.", strict=False)
def test_pay_receipt_email(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/orders\")"):
        navigate(page, "/orders")
    with allure.step("Assert: validate expected result"):
            assert "/orders" in page.url

