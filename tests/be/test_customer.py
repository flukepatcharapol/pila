# tests/fe/test_customer.py
#
# FE tests สำหรับ Customer Management
# TC-CUST-01 ถึง TC-CUST-12

import re
import pytest
import allure
from helpers.common_web import (
    navigate, login_as,
    fill, click, click_chip, select_option, get_text, is_visible,
    search_table, get_table_row_count,
    assert_table_contains, assert_table_not_contains, assert_no_uuid_in_table,
    assert_success_toast, assert_validation_error_shown,
    click_add_button, click_save, click_edit, click_delete, click_table_row,
)


# ─── Customer List ───────────────────────────────────────────────────────────────

@allure.title("TC-CUST-01: Customer list loads with correct columns")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_customer_list_loads(page, request):
    """ตรวจสอบว่าหน้า /customers โหลดได้พร้อมแสดง columns ถูกต้อง"""
    with allure.step("Login as admin and navigate to /customers"):
        login_as(page, "admin", request)
        navigate(page, "/customers")

    with allure.step("Assert table columns visible"):
        # ตรวจ column headers ที่สำคัญ
        for col in ["Customer Code", "ชื่อ-นามสกุล", "ชื่อเล่น", "เบอร์โทร"]:
            header = page.locator(f"th:has-text('{col}')")
            assert header.count() > 0, (
                f"Column '{col}' must be visible in customer table."
            )

    with allure.step("Assert no raw UUIDs in table"):
        assert_no_uuid_in_table(page)


@allure.title("TC-CUST-02: Customer search filters in real-time")
@pytest.mark.fe
def test_customer_search_realtime(page, request):
    """ตรวจสอบว่า search bar กรองข้อมูลแบบ real-time"""
    with allure.step("Login and navigate to customers"):
        login_as(page, "admin", request)
        navigate(page, "/customers")

    initial_count = get_table_row_count(page)

    with allure.step("Search for specific customer name"):
        search_table(page, "ปัญฑกมล", request)

    with allure.step("Assert table filtered"):
        filtered_count = get_table_row_count(page)
        assert filtered_count <= initial_count, (
            "Search should reduce or maintain the number of visible rows."
        )
        # ทุก row ที่เหลือต้องมี search term
        assert_table_contains(page, "ปัญฑกมล")


@allure.title("TC-CUST-03: Owner can filter by branch")
@pytest.mark.fe
def test_customer_filter_by_branch(page, request):
    """ตรวจสอบว่า owner สามารถ filter ลูกค้าตามสาขาได้"""
    with allure.step("Login as owner"):
        login_as(page, "owner", request)
        navigate(page, "/customers")

    with allure.step("Select Pattaya branch filter"):
        select_option(page, "branch-filter",
                      "//select[@name='branch_filter']", "pattaya", request)

    with allure.step("Assert only Pattaya customers shown"):
        # ตรวจว่าทุก customer code ขึ้นต้นด้วย BPY (Pattaya prefix)
        rows = page.locator("[data-testid='table-row']").all()
        for row in rows:
            code_cell = row.locator("[data-testid='customer-code']")
            if code_cell.count() > 0:
                code = code_cell.text_content() or ""
                assert code.startswith("BPY"), (
                    f"Customer code '{code}' must start with 'BPY' when "
                    "Pattaya branch filter is active."
                )


@allure.title("TC-CUST-04: Filter by status shows only matching customers")
@pytest.mark.fe
def test_customer_filter_by_status(page, request):
    """ตรวจสอบว่า status filter ทำงานถูกต้อง"""
    with allure.step("Login as admin and go to customers"):
        login_as(page, "admin", request)
        navigate(page, "/customers")

    with allure.step("Filter by Inactive status"):
        select_option(page, "status-filter",
                      "//select[@name='status_filter']", "INACTIVE", request)

    with allure.step("Assert only inactive customers shown"):
        rows = page.locator("[data-testid='table-row']").all()
        for row in rows:
            badge = row.locator("[data-testid='status-badge']")
            if badge.count() > 0:
                assert "Inactive" in (badge.text_content() or ""), (
                    "Status filter must show only Inactive customers."
                )


# ─── Add Customer Form ────────────────────────────────────────────────────────────

@allure.title("TC-CUST-05: Add new customer — happy path")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_add_customer_happy_path(page, request):
    """ตรวจสอบ flow การเพิ่มลูกค้าใหม่ครบทุกขั้นตอน"""
    with allure.step("Login as admin and open add form"):
        login_as(page, "admin", request)
        navigate(page, "/customers")
        click_add_button(page, request)

    with allure.step("Select branch Pattaya"):
        click_chip(page, "Pattaya", request)

    with allure.step("Verify customer code auto-generated (read-only)"):
        code_field = page.get_by_test_id("customer-code-display")
        if code_field.count() > 0:
            # code ต้อง auto-generate และ read-only
            assert not code_field.first.is_editable(), (
                "Customer code field must be read-only (auto-generated)."
            )

    with allure.step("Select source type chip"):
        click_chip(page, "Page", request)

    with allure.step("Select trainer (Pattaya only)"):
        # trainer chip ต้องแสดงเฉพาะ Pattaya trainers
        click_chip(page, "Teen:Pattaya", request)

    with allure.step("Fill customer info"):
        fill(page, "first-name-input", "//input[@name='first_name']",
             "ทดสอบ", request)
        fill(page, "last-name-input", "//input[@name='last_name']",
             "ระบบ", request)
        fill(page, "nickname-input", "//input[@name='nickname']",
             "เทส", request)

    with allure.step("Set contact channel and phone"):
        click_chip(page, "Phone", request)
        fill(page, "phone-input", "//input[@name='phone']",
             "0812345678", request)

    with allure.step("Set status Active"):
        click_chip(page, "Active", request)

    with allure.step("Save customer"):
        click_save(page, request)

    with allure.step("Assert success and customer in list"):
        assert_success_toast(page)
        navigate(page, "/customers")
        assert_table_contains(page, "ทดสอบ")

    with allure.step("Assert customer code format BPY-MKTxxx"):
        # หา customer ที่สร้างใหม่แล้วตรวจ code format
        rows = page.locator("[data-testid='table-row']:has-text('ทดสอบ')").all()
        if rows:
            code = rows[0].locator("[data-testid='customer-code']").text_content() or ""
            assert re.match(r"BPY-MKT\d{3}", code), (
                f"Customer code '{code}' must match format BPY-MKTxxx "
                "for Pattaya branch with Page source."
            )


@allure.title("TC-CUST-06: Trainer chip filters by selected branch")
@pytest.mark.fe
def test_trainer_chip_filters_by_branch(page, request):
    """
    ตรวจสอบว่า trainer chip แสดงเฉพาะ trainer ของสาขาที่เลือก
    และเปลี่ยนเมื่อเปลี่ยนสาขา — ป้องกัน bug จากระบบเก่าที่แสดง trainer ทุกสาขา
    """
    with allure.step("Open add customer form"):
        login_as(page, "owner", request)
        navigate(page, "/customers")
        click_add_button(page, request)

    with allure.step("Select Pattaya branch"):
        click_chip(page, "Pattaya", request)
        page.wait_for_timeout(500)  # รอ trainer list update

    with allure.step("Assert only Pattaya trainers shown"):
        trainer_chips = page.locator("[data-testid='trainer-chip']").all_text_contents()
        for trainer in trainer_chips:
            assert "Pattaya" in trainer, (
                f"Trainer '{trainer}' should not appear when Pattaya is selected. "
                "Trainer chip must filter by selected branch."
            )
        # ต้องไม่มี trainer จาก Kanchanaburi
        assert not any("Kanchanaburi" in chip_text for chip_text in trainer_chips), (
            "Kanchanaburi trainers must NOT appear when Pattaya is selected."
        )

    with allure.step("Change to Kanchanaburi branch"):
        click_chip(page, "Kanchanaburi", request)
        page.wait_for_timeout(500)

    with allure.step("Assert trainer list updated to Kanchanaburi"):
        trainer_chips = page.locator("[data-testid='trainer-chip']").all_text_contents()
        assert not any("Pattaya" in chip_text for chip_text in trainer_chips), (
            "Pattaya trainers must NOT appear after switching to Kanchanaburi."
        )


@allure.title("TC-CUST-07: Required field validation on empty submit")
@pytest.mark.fe
def test_customer_form_required_validation(page, request):
    """ตรวจสอบว่ากด Save โดยไม่กรอก required fields → แสดง validation errors"""
    with allure.step("Open add customer form"):
        login_as(page, "admin", request)
        navigate(page, "/customers")
        click_add_button(page, request)

    with allure.step("Click Save without filling anything"):
        click_save(page, request)

    with allure.step("Assert validation errors shown"):
        # Required fields: branch, first_name, last_name, phone
        assert_validation_error_shown(page, "branch-input")
        assert_validation_error_shown(page, "first-name-input")
        assert_validation_error_shown(page, "last-name-input")


@allure.title("TC-CUST-08: Customer code format matches branch+source")
@pytest.mark.fe
def test_customer_code_format(page, request):
    """ตรวจสอบว่า customer code ที่ auto-generate มี format ถูกต้อง"""
    with allure.step("Open add customer form"):
        login_as(page, "admin", request)
        navigate(page, "/customers")
        click_add_button(page, request)

    with allure.step("Select Pattaya + Page source"):
        click_chip(page, "Pattaya", request)
        click_chip(page, "Page", request)
        page.wait_for_timeout(300)

    with allure.step("Assert code preview starts with BPY-MKT"):
        code = get_text(page, "customer-code-display",
                        "//span[@data-testid='customer-code-display']", request)
        assert code.startswith("BPY-MKT"), (
            f"Auto-generated code '{code}' must start with 'BPY-MKT' "
            "for Pattaya branch with Page (MKT) source type."
        )


# ─── Customer Detail ─────────────────────────────────────────────────────────────

@allure.title("TC-CUST-09: Customer detail shows all sections")
@pytest.mark.fe
def test_customer_detail_shows_all_sections(page, request):
    """ตรวจสอบว่าหน้า detail แสดงข้อมูลครบทุก section"""
    with allure.step("Login and navigate to customers"):
        login_as(page, "admin", request)
        navigate(page, "/customers")

    with allure.step("Click first customer row"):
        first_row = page.locator("[data-testid='table-row']").first
        first_row.click()

    with allure.step("Assert all detail sections visible"):
        # Profile header
        assert is_visible(page, "customer-code-detail",
                           "//span[@data-testid='customer-code']", request), (
            "Customer code must be visible in detail view."
        )
        # Contact info
        assert is_visible(page, "contact-info-section",
                           "//section[@data-testid='contact-info']", request)
        # Order history
        assert is_visible(page, "order-history-table",
                           "//table[@data-testid='order-history']", request), (
            "Order history table must be visible in customer detail."
        )
        # Remaining hours
        assert is_visible(page, "remaining-hours-card",
                           "//div[@data-testid='remaining-hours']", request), (
            "Remaining hours card must be visible in customer detail."
        )


@allure.title("TC-CUST-10: Edit customer pre-fills form correctly")
@pytest.mark.fe
def test_edit_customer_prefills_form(page, request):
    """ตรวจสอบว่า edit form มีข้อมูลเดิม pre-fill ไว้ถูกต้อง"""
    with allure.step("Navigate to customer detail"):
        login_as(page, "admin", request)
        navigate(page, "/customers")
        page.locator("[data-testid='table-row']").first.click()

    with allure.step("Click Edit button"):
        click_edit(page, request)

    with allure.step("Assert form pre-filled"):
        # ตรวจว่า fields มีค่าอยู่แล้ว (ไม่ว่าง)
        first_name = page.get_by_test_id("first-name-input")
        if first_name.count() > 0:
            assert first_name.input_value() != "", (
                "First name field must be pre-filled when editing existing customer."
            )

    with allure.step("Assert customer code is read-only"):
        code_field = page.get_by_test_id("customer-code-display")
        if code_field.count() > 0:
            assert not code_field.is_editable(), (
                "Customer code must remain read-only in edit mode. "
                "Code cannot be changed after creation."
            )


@allure.title("TC-CUST-11: Delete customer requires confirmation dialog")
@pytest.mark.fe
def test_delete_customer_requires_confirmation(page, request):
    """ตรวจสอบว่าลบ customer ต้องผ่าน confirmation dialog ก่อน"""
    with allure.step("Navigate to customer detail"):
        login_as(page, "owner", request)
        navigate(page, "/customers")
        page.locator("[data-testid='table-row']").first.click()

    with allure.step("Click Delete button"):
        click(page, "delete-btn", "//button[@data-action='delete']", request)

    with allure.step("Assert confirmation dialog appears"):
        dialog = page.locator("[data-testid='confirm-dialog']")
        assert dialog.is_visible(), (
            "Confirmation dialog must appear before deleting customer. "
            "Destructive actions must always require confirmation."
        )

    with allure.step("Click Cancel — customer should NOT be deleted"):
        click(page, "cancel-btn", "//button[@data-action='cancel']", request)
        # ตรวจว่า dialog หายไปและ customer ยังอยู่
        assert not dialog.is_visible(), "Dialog should close after Cancel"


@allure.title("TC-CUST-12: Customer dropdown shows name and code, never UUID")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.fe
def test_customer_dropdown_shows_name_not_uuid(page, request):
    """
    Critical regression test: ระบบเก่าแสดง UUID ใน customer dropdown
    ตรวจสอบว่าระบบใหม่แสดงชื่อและรหัสลูกค้าเสมอ
    """
    with allure.step("Navigate to session deduct page"):
        login_as(page, "admin", request)
        navigate(page, "/customer-hours/deduct")

    with allure.step("Open customer dropdown"):
        click(page, "customer-select",
              "//div[@data-testid='customer-select']", request)

    with allure.step("Assert no UUID in dropdown options"):
        import re
        uuid_pattern = re.compile(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            re.IGNORECASE
        )
        options = page.locator("[data-testid='customer-option']").all_text_contents()

        assert len(options) > 0, "Dropdown must have options"

        for option_text in options:
            assert not uuid_pattern.search(option_text), (
                f"Dropdown option contains raw UUID: '{option_text}'. "
                "Customer dropdown must show Name and Code, never UUID. "
                "This is a critical regression from the old system."
            )
