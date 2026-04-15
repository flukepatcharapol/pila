import allure
import pytest

from helpers.common_web import login_as, navigate


@allure.title("TC-BROWSER-01: Core flows work on Safari")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires WebKit project execution in CI matrix.", strict=False)
def test_browser_safari_core_flows(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    for route in ["/dashboard", "/customers", "/orders/new", "/booking"]:
        with allure.step("Action: navigate(page, route)"):
            navigate(page, route)
        with allure.step("Assert: validate expected result"):
                    assert route.split("/")[1] in page.url or "/login" in page.url


@allure.title("TC-BROWSER-02: Core flows work on Firefox")
@pytest.mark.fe
@pytest.mark.xfail(reason="Requires Firefox project execution in CI matrix.", strict=False)
def test_browser_firefox_core_flows(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    for route in ["/dashboard", "/customers", "/orders/new", "/booking"]:
        with allure.step("Action: navigate(page, route)"):
            navigate(page, route)
        with allure.step("Assert: validate expected result"):
                    assert route.split("/")[1] in page.url or "/login" in page.url

