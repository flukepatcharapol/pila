import allure
import pytest

from helpers.common_web import (
    login_as,
    navigate,
    assert_sidebar_has_labels,
    assert_sidebar_lacks_labels,
)


@allure.title("TC-NAV-01: Sidebar renders correct items for Owner role")
@pytest.mark.fe
def test_nav_owner_sidebar_items(page, request):
    with allure.step("Action: login_as(page, role=\"owner\", request=request)"):
        login_as(page, role="owner", request=request)
    with allure.step("Action: assert owner sidebar labels"):
        assert_sidebar_has_labels(
            page,
            ["Dashboard", "เบิกเซสชัน", "ตารางจอง", "ลูกค้า", "ผู้ใช้งาน", "สิทธิ์การเข้าถึง", "ช่วยเหลือ"],
        )


@allure.title("TC-NAV-02: Sidebar restricts items for Master (Trainer) role")
@pytest.mark.fe
def test_nav_trainer_sidebar_restrictions(page, request):
    with allure.step("Action: login_as(page, role=\"trainer\", request=request)"):
        login_as(page, role="trainer", request=request)
    with allure.step("Action: assert_sidebar_lacks_labels(page, [\"ผู้ใช้งาน\", \"สิทธิ์การเข้าถึง\", \"สาขา\"])"):
        assert_sidebar_lacks_labels(page, ["ผู้ใช้งาน", "สิทธิ์การเข้าถึง", "สาขา"])


@allure.title("TC-NAV-03: Active branch shown in sidebar")
@pytest.mark.fe
def test_nav_active_branch_label_visible(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    branch_label = page.locator("aside:has-text('สาขาที่เลือก')")
    with allure.step("Assert: validate expected result"):
            assert branch_label.count() > 0 and branch_label.first.is_visible(), (
                "Sidebar should show active branch section label."
            )


@allure.title("TC-NAV-04: Active state on current route")
@pytest.mark.fe
def test_nav_active_route_state(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/customers\")"):
        navigate(page, "/customers")
    active_link = page.locator("aside a[aria-current='page']")
    with allure.step("Assert: validate expected result"):
            assert active_link.count() > 0, "Current route should set aria-current=page on sidebar link."
    with allure.step("Assert: validate expected result"):
            assert "ลูกค้า" in (active_link.first.text_content() or ""), "Customer route should highlight customer menu."


@allure.title("TC-NAV-05: Feature toggle overlay")
@pytest.mark.fe
@pytest.mark.xfail(reason="Feature toggle overlay path not wired in current FE routes.", strict=False)
def test_nav_feature_toggle_overlay(page, request):
    with allure.step("Action: login_as(page, role=\"admin\", request=request)"):
        login_as(page, role="admin", request=request)
    with allure.step("Action: navigate(page, \"/booking\")"):
        navigate(page, "/booking")
    overlay = page.get_by_test_id("feature-disabled-overlay")
    with allure.step("Assert: validate expected result"):
            assert overlay.is_visible()
    with allure.step("Assert: validate expected result"):
            assert "ฟีเจอร์นี้ไม่พร้อมใช้งาน" in (overlay.text_content() or "")

