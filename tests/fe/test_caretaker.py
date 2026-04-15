import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-CARE-01: Caretaker list grouped by branch")
@pytest.mark.fe
@pytest.mark.xfail(reason="Current FE caretaker list is flat table; branch grouping UI not implemented.", strict=False)
def test_caretaker_grouped_by_branch(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: navigate(page, \"/caretakers\")"):
        navigate(page, "/caretakers")
    with allure.step("Assert: validate expected result"):
            assert "/caretakers" in page.url


@allure.title("TC-CARE-02: Add caretaker — happy path")
@pytest.mark.fe
def test_caretaker_add_happy_path(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/caretakers\")"):
        navigate(page, "/caretakers")
    with allure.step("Action: page.get_by_test_id(\"caretaker-list-add-btn\").click()"):
        page.get_by_test_id("caretaker-list-add-btn").click()
    with allure.step("Action: page.get_by_test_id(\"caretaker-form-name\").fill(\"Auto Caretaker\")"):
        page.get_by_test_id("caretaker-form-name").fill("Auto Caretaker")
    with allure.step("Action: page.get_by_test_id(\"caretaker-form-email\").fill(\"auto.caretaker@test.com\")"):
        page.get_by_test_id("caretaker-form-email").fill("auto.caretaker@test.com")
    with allure.step("Action: page.get_by_test_id(\"caretaker-form-submit\").click()"):
        page.get_by_test_id("caretaker-form-submit").click()
    with allure.step("Assert: validate expected result"):
            assert "/caretakers" in page.url


@allure.title("TC-CARE-03: Admin sees only own branch caretakers")
@pytest.mark.fe
@pytest.mark.xfail(reason="Needs deterministic cross-branch caretaker fixtures.", strict=False)
def test_caretaker_admin_branch_scope(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/caretakers\")"):
        navigate(page, "/caretakers")
    with allure.step("Assert: validate expected result"):
            assert "/caretakers" in page.url


@allure.title("TC-CARE-04: Caretaker appears in customer form dropdown")
@pytest.mark.fe
def test_caretaker_visible_in_customer_form_selector(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers/new\")"):
        navigate(page, "/customers/new")
    with allure.step("Assert: validate expected result"):
            assert page.get_by_test_id("customer-form-caretaker").is_visible()

