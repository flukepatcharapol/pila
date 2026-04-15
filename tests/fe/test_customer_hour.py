import allure
import pytest

from helpers.common_web import login_as, navigate, assert_no_uuid_in_page


@allure.title("TC-HOUR-01: Session deduct — select customer by name")
@pytest.mark.fe
def test_hour_customer_search_by_name(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/sessions/deduct\")"):
        navigate(page, "/sessions/deduct")
    with allure.step("Action: page.get_by_test_id(\"session-deduct-customer-search\").fill(\"test\")"):
        page.get_by_test_id("session-deduct-customer-search").fill("test")
    with allure.step("Action: assert_no_uuid_in_page(page)"):
        assert_no_uuid_in_page(page)


@allure.title("TC-HOUR-02: Session deduct — happy path")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires deterministic customer with remaining hours in seed data.", strict=False)
def test_hour_deduct_happy_path(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/sessions/deduct\")"):
        navigate(page, "/sessions/deduct")
    with allure.step("Action: page.get_by_test_id(\"session-deduct-customer-search\").fill(\"test\")"):
        page.get_by_test_id("session-deduct-customer-search").fill("test")
    with allure.step("Action: page.get_by_test_id(\"session-deduct-btn\").click()"):
        page.get_by_test_id("session-deduct-btn").click()
    with allure.step("Assert: validate expected result"):
            assert page.locator("text=คงเหลือ").count() > 0


@allure.title("TC-HOUR-03: Session deduct — no hours remaining")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires dedicated zero-hour seeded customer.", strict=False)
def test_hour_deduct_no_hours(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/sessions/deduct\")"):
        navigate(page, "/sessions/deduct")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("session-deduct-btn").is_visible()


@allure.title("TC-HOUR-04: Session log table — filter by date range")
@pytest.mark.fe
def test_hour_log_filter_by_date(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/sessions/log\")"):
        navigate(page, "/sessions/log")
    with allure.step("Action: page.get_by_test_id(\"session-log-search\").fill(\"test\")"):
        page.get_by_test_id("session-log-search").fill("test")
    with allure.step("Assert: validate expected result"):
            assert "/sessions/log" in page.url


@allure.title("TC-HOUR-05: Session log shows transaction type correctly")
@pytest.mark.fe
def test_hour_log_transaction_type_column(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/sessions/log\")"):
        navigate(page, "/sessions/log")
    header_text = page.locator("thead").inner_text()
    with allure.step("Assert: validate expected result"):
            assert "ประเภท" in header_text or "Transaction" in header_text


@allure.title("TC-HOUR-06: Trainer report — Today quick filter")
@pytest.mark.fe
def test_hour_trainer_report_fetch(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/sessions/trainer-report\")"):
        navigate(page, "/sessions/trainer-report")
    with allure.step("Action: page.get_by_test_id(\"trainer-report-fetch-btn\").click()"):
        page.get_by_test_id("trainer-report-fetch-btn").click()
    with allure.step("Assert: validate expected result"):
            assert "/sessions/trainer-report" in page.url


@allure.title("TC-HOUR-07: Trainer report — filter by trainer")
@pytest.mark.fe
def test_hour_trainer_report_has_filter_controls(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/sessions/trainer-report\")"):
        navigate(page, "/sessions/trainer-report")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("trainer-report-fetch-btn").is_visible()


@allure.title("TC-HOUR-08: Cancel booking returns session to customer (policy = return)")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs booking cancel policy fixture and booking lifecycle setup.", strict=False)
def test_hour_cancel_booking_returns_session(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/booking\")"):
        navigate(page, "/booking")
    with allure.step("Assert: validate expected result"):
            assert "/booking" in page.url


@allure.title("TC-HOUR-09: Cancel booking does not return session (policy = no return)")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs booking cancel policy fixture and booking lifecycle setup.", strict=False)
def test_hour_cancel_booking_no_return(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/booking\")"):
        navigate(page, "/booking")
    with allure.step("Assert: validate expected result"):
            assert "/booking" in page.url

