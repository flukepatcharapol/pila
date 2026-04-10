# FE Test Cases — Playwright (Python)
## Pila Studio Management

> **Framework:** Playwright + pytest (Python)
> **Coverage:** All pages, user flows, role-based access, form validation, error states
> **Date:** 2026-04-05

---

## Test Structure

```
tests/
  fe/
    test_auth.py
    test_dashboard.py
    test_customer.py
    test_order.py
    test_customer_hour.py
    test_trainer.py
    test_package.py
    test_booking.py
    test_user.py
    test_permission.py
    test_settings.py
    conftest.py          # fixtures: browser, login helpers, role contexts
```

---

## Fixtures & Helpers (conftest.py)

```python
# Roles: developer | owner | branch_master | admin | trainer
# Helper: login_as(page, role) → handles email+password+PIN entry
# Helper: assert_toast(page, text) → checks success/error toast
# Helper: assert_table_row(page, text) → checks row in data table
```

---

## TC-AUTH — Authentication

### TC-AUTH-01: Login with valid credentials
- **File:** `test_auth.py`
- **Steps:**
  1. Navigate to `/login`
  2. Enter valid email and password
  3. Click submit
- **Expected:** Redirected to `/pin` page; PIN input visible

### TC-AUTH-02: Login with invalid password
- **Steps:**
  1. Navigate to `/login`
  2. Enter valid email + wrong password
  3. Click submit
- **Expected:** Error message shown; still on `/login`; no redirect

### TC-AUTH-03: Login with empty fields
- **Steps:**
  1. Navigate to `/login`
  2. Click submit without filling fields
- **Expected:** Validation error on both fields; no network request sent

### TC-AUTH-04: PIN entry with valid PIN
- **Precondition:** Logged in, on `/pin`
- **Steps:**
  1. Enter correct 6-digit PIN
  2. Click confirm
- **Expected:** Redirected to `/dashboard`

### TC-AUTH-05: PIN entry with wrong PIN
- **Steps:**
  1. Enter incorrect PIN
  2. Click confirm
- **Expected:** Error message displayed; input cleared; stays on `/pin`

### TC-AUTH-06: PIN session expiry re-prompt
- **Steps:**
  1. Login successfully and enter PIN
  2. Simulate 5-hour session expiry (manipulate cookie/token via API)
  3. Navigate to any protected route
- **Expected:** Redirected to `/pin` (not `/login`); PIN re-entry prompt shown

### TC-AUTH-07: Forgot PIN — OTP flow
- **Steps:**
  1. On `/pin`, click "Forgot PIN?"
  2. Navigate to `/pin/reset`
  3. Enter OTP from email field (mock OTP in test env)
  4. Enter new PIN + confirm
  5. Submit
- **Expected:** PIN reset success message; redirected to `/pin`

### TC-AUTH-08: Unauthenticated access redirect
- **Steps:**
  1. Open `/customers` without logging in
- **Expected:** Redirected to `/login`

---

## TC-NAV — Navigation & Sidebar

### TC-NAV-01: Sidebar renders correct items for Owner role
- **Steps:**
  1. Login as owner
  2. Inspect sidebar
- **Expected:** All menu groups visible (Overview, Operations, Records, Management, System, Help)

### TC-NAV-02: Sidebar restricts items for Master (Trainer) role
- **Steps:**
  1. Login as master
  2. Inspect sidebar
- **Expected:** Only own-data menus visible; User/Permission/Branch Config hidden

### TC-NAV-03: Active branch shown in sidebar
- **Steps:**
  1. Login as admin (Pattaya branch)
  2. Check sidebar header area
- **Expected:** "Pattaya" branch label visible

### TC-NAV-04: Active state on current route
- **Steps:**
  1. Navigate to `/customers`
  2. Inspect sidebar Customer link
- **Expected:** Customer menu item has active styling (color/background change)

### TC-NAV-05: Feature toggle overlay
- **Steps:**
  1. Owner disables a module (e.g., Booking) via feature toggle
  2. Admin navigates to `/booking`
- **Expected:** Overlay "ฟีเจอร์นี้ไม่พร้อมใช้งาน" shown on page

---

## TC-DASH — Dashboard

### TC-DASH-01: Dashboard loads for Trainer role
- **Steps:**
  1. Login as master
  2. Navigate to `/dashboard`
- **Expected:** Cards shown: Hours trained (today/MTD), Customer count, Bookings

### TC-DASH-02: Dashboard loads for Admin role
- **Steps:**
  1. Login as admin
  2. Navigate to `/dashboard`
- **Expected:** Cards shown: Orders today, Sessions deducted today

### TC-DASH-03: Dashboard loads for Owner role — branch selector visible
- **Steps:**
  1. Login as owner
  2. Navigate to `/dashboard`
- **Expected:** Branch selector dropdown visible; "All Branches" tab shown

### TC-DASH-04: Time range filter changes chart data
- **Steps:**
  1. Login as owner
  2. On dashboard, select "This Month" filter
  3. Then select "Today"
- **Expected:** Chart and stat cards update each time; no page reload

### TC-DASH-05: Dashboard shows loading skeleton before data
- **Steps:**
  1. Throttle network to slow 3G
  2. Navigate to `/dashboard`
- **Expected:** Skeleton/shimmer placeholders visible before data loads

---

## TC-CUST — Customer Management

### TC-CUST-01: Customer list loads and displays data
- **Steps:**
  1. Login as admin
  2. Navigate to `/customers`
- **Expected:** Table with columns (Customer Code, Name, Nickname, Phone, Branch, Status) populated

### TC-CUST-02: Customer search by name
- **Steps:**
  1. On `/customers`, type partial name in search bar
- **Expected:** Table filters in real-time; only matching rows shown

### TC-CUST-03: Customer filter by branch (Owner)
- **Steps:**
  1. Login as owner
  2. On `/customers`, select branch "Pattaya"
- **Expected:** Only Pattaya customers shown

### TC-CUST-04: Customer filter by status
- **Steps:**
  1. Select "Inactive" from status filter
- **Expected:** Only inactive customers shown

### TC-CUST-05: Add new customer — happy path
- **Steps:**
  1. Click "Add Customer"
  2. Select branch "Pattaya"
  3. Verify customer code is auto-generated (read-only)
  4. Select source type chip
  5. Select trainer chip (filtered to Pattaya trainers only)
  6. Fill in First name, Last name, Nickname
  7. Select contact channel (Phone), enter phone number
  8. Set status Active
  9. Upload profile photo
  10. Click Save
- **Expected:** Success toast shown; customer appears in list with correct code format `BPY-XXXNNN`

### TC-CUST-06: Trainer chip filters by selected branch
- **Steps:**
  1. In new customer form, select branch "Pattaya"
  2. Open trainer chip selector
- **Expected:** Only Pattaya trainers listed (no trainers from other branches)
  3. Change branch to "Kanchanaburi"
  4. Open trainer chip selector again
- **Expected:** Trainer list updates to Kanchanaburi trainers only

### TC-CUST-07: Customer form validation — required fields
- **Steps:**
  1. Open new customer form
  2. Click Save without filling any fields
- **Expected:** Validation errors on required fields (Branch, First name, Last name, Phone)

### TC-CUST-08: Customer code format validation
- **Steps:**
  1. Add customer to branch "Pattaya" with source type "Page" (MKT)
- **Expected:** Generated code starts with `BPY-MKT` followed by running number

### TC-CUST-09: Customer detail view shows all sections
- **Steps:**
  1. Click on a customer row
- **Expected:** Detail view shows: profile photo, name, code, status badge, contact info, trainer, caretaker, order history table, remaining session hours

### TC-CUST-10: Edit customer — pre-fills form correctly
- **Steps:**
  1. From customer detail, click Edit
- **Expected:** All existing fields pre-filled correctly; customer code field is read-only

### TC-CUST-11: Delete customer requires confirmation
- **Steps:**
  1. From customer detail, click Delete
- **Expected:** Confirmation dialog appears before deletion proceeds

### TC-CUST-12: Customer dropdown in other forms shows name, not UUID
- **Steps:**
  1. Open Customer Hour Deduct page
  2. Open customer dropdown
- **Expected:** Each option shows customer name and code — no raw UUIDs visible

---

## TC-ORDER — Order Management

### TC-ORDER-01: Order list loads with correct columns
- **Steps:**
  1. Navigate to `/orders`
- **Expected:** Columns: Date, Customer Code, Customer Name, Package, Hours, Payment Status, Branch

### TC-ORDER-02: Order list filter by date range
- **Steps:**
  1. Set date range to last 7 days
- **Expected:** Only orders within range shown

### TC-ORDER-03: Order list shows outstanding balance badge
- **Steps:**
  1. Navigate to `/orders`
- **Expected:** Rows with unpaid balance show a visible badge/indicator

### TC-ORDER-04: Add new order — happy path
- **Steps:**
  1. Click "Add Order"
  2. Set order date
  3. Search and select a customer
  4. Verify trainer and caretaker auto-filled from customer profile
  5. Select an active package (chip selector)
  6. Set hours via stepper
  7. Set bonus hours via stepper
  8. Select payment method (Bank Transfer)
  9. Enter total price
  10. Click Save
- **Expected:** Success toast; order appears in list; sessions allocated to customer

### TC-ORDER-05: Package chip only shows active + branch-matched
- **Steps:**
  1. In order form, select customer from Pattaya branch
  2. Open package chip selector
- **Expected:** Only active packages scoped to Pattaya (or All branches) are shown; expired/inactive excluded

### TC-ORDER-06: Trainer auto-fills from customer profile
- **Steps:**
  1. Select customer in order form
- **Expected:** Trainer chip pre-populated with customer's assigned trainer

### TC-ORDER-07: Order form validation
- **Steps:**
  1. Open new order form, click Save immediately
- **Expected:** Validation errors on required fields (Date, Customer, Package, Payment method)

### TC-ORDER-08: Order detail view shows payment breakdown
- **Steps:**
  1. Click on an order row
- **Expected:** Payment section shows total, paid, outstanding, installment plan if applicable

---

## TC-HOUR — Customer Hour System

### TC-HOUR-01: Session deduct — select customer by name
- **Steps:**
  1. Navigate to `/customer-hours/deduct`
  2. Open customer dropdown
  3. Type customer name
- **Expected:** Matching customers shown by name and code; NO UUID visible

### TC-HOUR-02: Session deduct — happy path
- **Steps:**
  1. Select branch chip
  2. Select customer
  3. Click Deduct
- **Expected:** Session deducted; history table updated with new row; remaining hours decremented

### TC-HOUR-03: Session deduct — no hours remaining
- **Steps:**
  1. Select a customer with 0 remaining hours
  2. Click Deduct
- **Expected:** Error shown "No remaining hours"; deduction blocked

### TC-HOUR-04: Session log table — filter by date range
- **Steps:**
  1. Navigate to `/customer-hours/log`
  2. Set date range filter
- **Expected:** Table updates to show only logs within range

### TC-HOUR-05: Session log shows transaction type correctly
- **Steps:**
  1. View session log
- **Expected:** Columns: Timestamp, Customer Code, Name, Transaction Type (Deduct/Add/Adjust), Before, Amount, After, Actor

### TC-HOUR-06: Trainer report — Today quick filter
- **Steps:**
  1. Navigate to `/customer-hours/trainer-report`
  2. Click "Today" button
- **Expected:** Summary cards and table update to today's data only

### TC-HOUR-07: Trainer report — filter by trainer
- **Steps:**
  1. Select specific trainer from trainer selector
- **Expected:** Table shows only training sessions by that trainer

---

## TC-PKG — Package Management

### TC-PKG-01: Package list loads with status badges
- **Steps:**
  1. Navigate to `/packages`
- **Expected:** Active (teal badge), Inactive (grey), Expired (red) badges visible

### TC-PKG-02: Add package — happy path
- **Steps:**
  1. Click "Add Package"
  2. Enter name, hours, type (Sale), price
  3. Set branch scope to "All"
  4. Click Save
- **Expected:** Package appears in list with correct status

### TC-PKG-03: Package with active period expires correctly
- **Steps:**
  1. Create package with active period ending yesterday
  2. View package list
- **Expected:** Package shows "Expired" badge

---

## TC-USER — User Management

### TC-USER-01: User list grouped by Active/Inactive
- **Steps:**
  1. Login as owner, navigate to `/users`
- **Expected:** Users grouped under "Active" and "Inactive" sections

### TC-USER-02: Role badge colors correct
- **Steps:**
  1. View user list
- **Expected:** Owner=deep-sea color, Admin=steel-blue, Master=teal

### TC-USER-03: Branch Manager cannot create users for other branches
- **Steps:**
  1. Login as admin (Branch Manager)
  2. Click "Add User"
  3. In branch selector
- **Expected:** Only own branch available in dropdown

### TC-USER-04: Slide-out detail panel
- **Steps:**
  1. Click on a user row
- **Expected:** Slide-out panel animates in from right with user details

---

## TC-PERM — Permission Management

### TC-PERM-01: Permission matrix displays toggle switches
- **Steps:**
  1. Login as owner, navigate to `/permissions`
- **Expected:** Matrix with toggle switches (not checkboxes) for each Module × Role cell

### TC-PERM-02: Toggle persists after page reload
- **Steps:**
  1. Toggle a permission off
  2. Reload page
- **Expected:** Toggle remains off

### TC-PERM-03: Permission change hides menu for affected role
- **Steps:**
  1. Owner disables "Package" view for Admin role
  2. Login as admin
- **Expected:** Package menu item not visible in sidebar

---

## TC-BOOK — Booking / Schedule

### TC-BOOK-01: Timetable renders 3-day view by default
- **Steps:**
  1. Navigate to `/booking`
- **Expected:** Grid shows today + 2 upcoming days; 30-min time slots visible

### TC-BOOK-02: Toggle to full week view
- **Steps:**
  1. Click "Full Week" toggle
- **Expected:** Grid expands to 7 columns; all days visible

### TC-BOOK-03: Color coding is correct
- **Steps:**
  1. View timetable with mixed bookings
- **Expected:** Staff schedule = blue; Customer booking = teal; Pending = amber

### TC-BOOK-04: Click empty slot opens booking popup
- **Steps:**
  1. Click on an empty 30-min slot
- **Expected:** Popup form appears with Date/Time pre-filled

### TC-BOOK-05: Trainer role can only schedule own slots
- **Steps:**
  1. Login as master (trainer)
  2. Try to add schedule for a different trainer
- **Expected:** Option not available; only own schedule editable

### TC-BOOK-06: Admin confirm booking — LINE notify prompt
- **Steps:**
  1. Login as admin
  2. Confirm a pending booking for customer with LINE
- **Expected:** Prompt appears: "Notify customer via LINE?" with Yes/No buttons

---

## TC-SET — Settings

### TC-SET-01: Language toggle switches between Thai and English
- **Steps:**
  1. Navigate to `/settings`
  2. Toggle language to English
- **Expected:** UI text switches to English immediately
  3. Toggle back to Thai
- **Expected:** UI text switches back to Thai

### TC-SET-02: Dark mode toggle
- **Steps:**
  1. Toggle dark mode on
- **Expected:** UI shifts to dark theme; surfaces darken
  2. Toggle off
- **Expected:** Returns to light theme

---

## TC-CROSS — Cross-Cutting Concerns

### TC-CROSS-01: All tables have working search
- **Steps:**
  1. On each list page (Customers, Orders, Trainers, Packages, Users)
  2. Type in search box
- **Expected:** Table filters without page reload

### TC-CROSS-02: All forms show loading state on submit
- **Steps:**
  1. Submit any form (throttle network)
- **Expected:** Submit button shows spinner/loading state; form not re-submittable

### TC-CROSS-03: Success toast on create/edit
- **Steps:**
  1. Successfully save any form
- **Expected:** Toast notification appears with success message; auto-dismisses

### TC-CROSS-04: Error toast on server error
- **Steps:**
  1. Mock server to return 500
  2. Submit any form
- **Expected:** Error toast shown; form data preserved

### TC-CROSS-05: No UUID shown anywhere in UI
- **Steps:**
  1. Audit all dropdowns and table cells across all pages
- **Expected:** No raw UUID strings visible to user anywhere

### TC-CROSS-06: Confirmation dialog on destructive actions
- **Steps:**
  1. Attempt to delete any entity (customer, order, trainer, etc.)
- **Expected:** Confirmation dialog with "Are you sure?" appears before action

### TC-CROSS-07: Responsive — tablet (768px) renders correctly
- **Steps:**
  1. Set viewport to 768×1024
  2. Navigate through main pages
- **Expected:** Sidebar collapses or adapts; tables scrollable; forms remain usable

### TC-CROSS-08: Thai text renders without clipping
- **Steps:**
  1. Enter Thai text in name fields
  2. View in table and detail views
- **Expected:** Thai characters render fully; no tone mark clipping; line-height adequate

---

## TC-PRINT — Signature Print

### TC-PRINT-01: Google Drive connection status shown
- **Steps:**
  1. Navigate to `/signature-print`
  2. Inspect Google Drive connection widget
- **Expected:** Widget shows connected account email OR "Not connected" prompt

### TC-PRINT-02: Storage widget shows correct usage
- **Steps:**
  1. On `/signature-print` with Google Drive connected
  2. Inspect storage widget
- **Expected:** Shows "X.X GB used of Y.X GB" — values match Google Drive API `about.get`

### TC-PRINT-03: Generate signature sheet — happy path
- **Steps:**
  1. Select an order
  2. Click "Generate"
- **Expected:** Google Sheet created; shareable link returned and displayed; file appears in Google Drive

### TC-PRINT-04: Generated link opens Google Sheet
- **Steps:**
  1. After generate, click returned link
- **Expected:** Google Sheet opens in new tab with correct format and layout

### TC-PRINT-05: Generate blocked when Google Drive not connected
- **Steps:**
  1. Disconnect Google Drive
  2. Click "Generate"
- **Expected:** Error/prompt shown to connect Google Account first; generation blocked

### TC-PRINT-06: Storage warning when Drive is near full
- **Steps:**
  1. Mock Google Drive storage to >90% full
  2. Navigate to `/signature-print`
- **Expected:** Warning banner shown "Storage is almost full" before generating

---

## TC-PAY — Payment Tracking

### TC-PAY-01: Order detail shows payment breakdown
- **Steps:**
  1. Click on any order
- **Expected:** Payment section shows: Total, Paid, Outstanding balance clearly

### TC-PAY-02: Outstanding balance badge in order list
- **Steps:**
  1. Navigate to `/orders`
  2. Find order with unpaid balance
- **Expected:** Orange/red badge visible on that row showing outstanding amount

### TC-PAY-03: Installment plan displays correctly
- **Steps:**
  1. Open order with installment plan
- **Expected:** Shows installment breakdown: งวดที่, ยอด, วันครบกำหนด, สถานะ (paid/unpaid)

### TC-PAY-04: Record installment payment — outstanding decreases
- **Steps:**
  1. Open order with outstanding balance
  2. Record a partial payment
- **Expected:** Outstanding balance decreases by recorded amount; history updated

### TC-PAY-05: Receipt/Invoice sent via email
- **Steps:**
  1. Save a new order
  2. Check mock email inbox in test env
- **Expected:** Receipt email received with correct order details

---

## TC-LOG — Activity Log

### TC-LOG-01: Activity log page loads with data
- **Steps:**
  1. Login as owner, navigate to `/activity-log`
- **Expected:** Table loads with columns: Timestamp, Actor, Action Type, Details, Branch

### TC-LOG-02: Filter by date range
- **Steps:**
  1. Set date range filter on activity log
- **Expected:** Only logs within range displayed

### TC-LOG-03: Filter by user/actor
- **Steps:**
  1. Select specific user from actor filter
- **Expected:** Only actions by that user shown

### TC-LOG-04: Filter by action type
- **Steps:**
  1. Select action type "Customer Hour Deduct"
- **Expected:** Only session deduction logs shown

### TC-LOG-05: Admin sees only own branch logs
- **Steps:**
  1. Login as admin (Pattaya)
  2. Navigate to `/activity-log`
- **Expected:** Only Pattaya branch activity shown; no other branch data

### TC-LOG-06: Owner sees all branch logs
- **Steps:**
  1. Login as owner
  2. Navigate to `/activity-log`
- **Expected:** Logs from all branches visible; branch column populated correctly

### TC-LOG-07: Session deduct action logged correctly
- **Steps:**
  1. Perform session deduction
  2. Check activity log
- **Expected:** New log entry: action = "Customer Hour Deduct", actor = current user, customer name shown

---

## TC-BRANCH — Branch Config

### TC-BRANCH-01: Branch list shows all branches with config
- **Steps:**
  1. Login as owner, navigate to `/branch-config`
- **Expected:** Table shows: Branch Name, Prefix, Source Types, Opening hours

### TC-BRANCH-02: Add new branch
- **Steps:**
  1. Click "Add Branch"
  2. Enter name, prefix, source types, opening/closing time
  3. Click Save
- **Expected:** New branch appears in list; customer code generates with new prefix correctly

### TC-BRANCH-03: Edit branch opening hours
- **Steps:**
  1. Edit a branch's opening/closing time
  2. Navigate to `/booking`
- **Expected:** Timetable time slots reflect updated opening hours

### TC-BRANCH-04: Edit source type prefix
- **Steps:**
  1. Edit source type code for a branch
  2. Add new customer with that source
- **Expected:** Generated customer code uses updated source type code

### TC-BRANCH-05: Only Owner can access Branch Config
- **Steps:**
  1. Login as admin
  2. Navigate to `/branch-config`
- **Expected:** Access denied or menu not visible

---

## TC-CARE — Caretaker Management

### TC-CARE-01: Caretaker list grouped by branch
- **Steps:**
  1. Login as owner, navigate to `/caretakers`
- **Expected:** List grouped by branch sections; each entry shows name, email, status

### TC-CARE-02: Add caretaker — happy path
- **Steps:**
  1. Click "Add Caretaker"
  2. Enter name, email, branch, status Active
  3. Click Save
- **Expected:** Caretaker appears in correct branch group

### TC-CARE-03: Admin sees only own branch caretakers
- **Steps:**
  1. Login as admin (Chachoengsao)
  2. Navigate to `/caretakers`
- **Expected:** Only Chachoengsao caretakers visible

### TC-CARE-04: Caretaker appears in customer form dropdown
- **Steps:**
  1. Open new customer form
  2. Select branch
  3. Open caretaker selector
- **Expected:** Only active caretakers of selected branch listed

---

## TC-HELP — Help Page

### TC-HELP-01: Help page loads correctly
- **Steps:**
  1. Navigate to `/help`
- **Expected:** Page shows User Manual section and LINE Contact section

### TC-HELP-02: User manual shows role-specific content
- **Steps:**
  1. Login as master (trainer)
  2. Navigate to `/help`
- **Expected:** Manual shows only sections relevant to trainer role (no admin/owner sections)

### TC-HELP-03: LINE Developer QR code visible
- **Steps:**
  1. Navigate to `/help`
- **Expected:** Developer QR image displayed correctly

### TC-HELP-04: LINE Branch group chat QR matches user's branch
- **Steps:**
  1. Login as admin (Kanchanaburi)
  2. Navigate to `/help`
- **Expected:** Kanchanaburi branch group chat QR shown (not other branches)

---

## TC-BOOK Additional — Booking / Schedule

### TC-BOOK-07: Admin can multi-select slots
- **Steps:**
  1. Login as admin
  2. On timetable, click and drag across multiple 30-min slots
- **Expected:** Multiple slots selected and highlighted; one booking form covers full range

### TC-BOOK-08: Trainer can multi-select own schedule slots
- **Steps:**
  1. Login as master
  2. Select multiple slots for own schedule
- **Expected:** Multiple slots saved as staff schedule

### TC-BOOK-09: Customer (external API) limited to contiguous slots same day
- **Steps:**
  1. Mock external API POST with non-contiguous slots
- **Expected:** API returns validation error; booking not created

### TC-BOOK-10: Cancel booking removes from timetable
- **Steps:**
  1. Login as admin
  2. Cancel a confirmed booking
- **Expected:** Booking removed from timetable immediately

### TC-BOOK-11: Cancel booking returns session based on policy
- **Steps:**
  1. Config cancel policy: hours returned = Yes
  2. Cancel a booking
- **Expected:** Customer's remaining hour count incremented by 1

### TC-BOOK-12: Cancel booking does not return session when policy = No
- **Steps:**
  1. Config cancel policy: hours returned = No
  2. Cancel a booking
- **Expected:** Customer's remaining hour count unchanged

### TC-BOOK-13: Pending booking from external API shown in amber
- **Steps:**
  1. Mock external API POST pending booking
  2. View timetable
- **Expected:** Pending slot shows in amber color

### TC-BOOK-14: Admin can confirm pending external booking
- **Steps:**
  1. View pending booking on timetable
  2. Click confirm
- **Expected:** Status changes to Confirmed; slot color changes to teal

### TC-BOOK-15: Customer without LINE — no notify button shown
- **Steps:**
  1. Confirm booking for customer without LINE registered
- **Expected:** "Notify customer via LINE?" prompt does NOT appear

---

## TC-DASH Additional — Dashboard

### TC-DASH-06: Dashboard loads for Branch Manager role
- **Steps:**
  1. Login as admin with Branch Manager role
  2. Navigate to `/dashboard`
- **Expected:** Cards shown: Total orders, Total revenue, Breakdown per admin, Breakdown per trainer

### TC-DASH-07: Branch Manager sees per-admin breakdown
- **Steps:**
  1. On Branch Manager dashboard
  2. Inspect admin breakdown section
- **Expected:** Each admin listed with order count and revenue

### TC-DASH-08: Owner switches branch — data updates
- **Steps:**
  1. Login as owner
  2. Select "Pattaya" from branch selector
- **Expected:** All dashboard cards update to Pattaya data only

### TC-DASH-09: Owner Overall tab shows all branches combined
- **Steps:**
  1. Login as owner
  2. Click "Overall" tab
- **Expected:** Summary shows combined data from all branches

---

## TC-PKG Additional — Package Management

### TC-PKG-04: Package scope "Selected branch" — only shows in that branch order form
- **Steps:**
  1. Create package scoped to "Pattaya" only
  2. Login as admin (Chachoengsao)
  3. Open order form → package chip
- **Expected:** Pattaya-scoped package NOT visible

### TC-PKG-05: Package scope "All branch" — shows in all branches
- **Steps:**
  1. Create package scoped to "All"
  2. Login as admin (Kanchanaburi)
  3. Open order form → package chip
- **Expected:** All-branch package IS visible

### TC-PKG-06: Package before active period — not shown in order form
- **Steps:**
  1. Create package with active period starting tomorrow
  2. Open order form → package chip
- **Expected:** Package not listed (not yet active)

### TC-PKG-07: Package after active period — shows Expired badge
- **Steps:**
  1. Create package with active period ending yesterday
  2. View package list
  3. Open order form → package chip
- **Expected:** Badge = "Expired"; not available in order form

---

## TC-HOUR Additional — Session

### TC-HOUR-08: Cancel booking returns session to customer (policy = return)
- **Steps:**
  1. Customer has N remaining hours
  2. Cancel booking with return policy
- **Expected:** Customer remaining hours = N+1

### TC-HOUR-09: Cancel booking does not return session (policy = no return)
- **Steps:**
  1. Customer has N remaining hours
  2. Cancel booking with no-return policy
- **Expected:** Customer remaining hours = N (unchanged)

---

## TC-SET Additional — Settings

### TC-SET-03: Dark mode persists after page reload
- **Steps:**
  1. Enable dark mode
  2. Reload page
- **Expected:** Dark mode still active; preference saved

### TC-SET-04: Language persists after page reload
- **Steps:**
  1. Switch to English
  2. Reload page
- **Expected:** UI still in English; preference saved

### TC-SET-05: Google Account connect flow
- **Steps:**
  1. Navigate to `/settings`
  2. Click "Connect Google Account"
  3. Complete OAuth flow (mock in test env)
- **Expected:** Connected account email displayed in settings

### TC-SET-06: Google Account disconnect
- **Steps:**
  1. With Google Account connected, click "Disconnect"
- **Expected:** Account removed; storage widget hidden; Signature Print shows connect prompt

### TC-SET-07: Google Drive storage displays correctly
- **Steps:**
  1. With Google connected, view settings
  2. Mock Drive API to return 5GB used / 15GB total
- **Expected:** Widget shows "5.0 GB used of 15.0 GB"

---

## TC-SEC — Security (FE)

### TC-SEC-01: Expired token redirects to login
- **Steps:**
  1. Login successfully
  2. Manually expire auth token via dev tools
  3. Navigate to any protected route
- **Expected:** Redirected to `/login` automatically

### TC-SEC-02: Sensitive data not in localStorage
- **Steps:**
  1. Login successfully
  2. Inspect localStorage and sessionStorage
- **Expected:** No password, raw token, or PIN stored in browser storage

### TC-SEC-03: XSS — script input does not execute
- **Steps:**
  1. Enter `<script>alert('xss')</script>` in any text field
  2. Save and view detail page
- **Expected:** Script not executed; displayed as plain text or sanitized

### TC-SEC-04: Unauthorized route access by role
- **Steps:**
  1. Login as master (trainer)
  2. Directly navigate to `/users` or `/branch-config`
- **Expected:** Redirected to `/403` or dashboard; page content not shown

---

## TC-PERSIST — State Persistence

### TC-PERSIST-01: Filter state preserved on back navigation
- **Steps:**
  1. Apply filters on `/customers` (branch=Pattaya, status=Active)
  2. Click into a customer detail
  3. Click browser back
- **Expected:** Filter state restored; same filtered results shown

### TC-PERSIST-02: Dark mode preference survives session
- **Steps:**
  1. Enable dark mode
  2. Close browser completely
  3. Reopen and navigate to app
- **Expected:** Dark mode still active

### TC-PERSIST-03: Language preference survives session
- **Steps:**
  1. Set language to English
  2. Close browser completely
  3. Reopen and navigate to app
- **Expected:** UI still in English

---

## TC-ERR — Error Handling

### TC-ERR-01: JS error boundary shows fallback UI
- **Steps:**
  1. Mock a React component to throw error
  2. Navigate to that page
- **Expected:** Fallback UI shown ("Something went wrong" + retry button); no white screen

### TC-ERR-02: Network timeout shows retry option
- **Steps:**
  1. Mock network request to timeout
  2. Navigate to any list page
- **Expected:** Error state shown with "Retry" button; clicking retry re-fetches

### TC-ERR-03: 401 Unauthorized redirects to login
- **Steps:**
  1. Mock API to return 401
  2. Perform any action
- **Expected:** Redirected to `/login` with session cleared

### TC-ERR-04: 403 Forbidden shows access denied page
- **Steps:**
  1. Mock API to return 403
  2. Navigate to restricted resource
- **Expected:** "ไม่มีสิทธิ์เข้าถึง" page shown; not a blank/crash screen

### TC-ERR-05: 404 Not Found shows 404 page
- **Steps:**
  1. Navigate to `/nonexistent-route`
- **Expected:** Custom 404 page shown with link back to dashboard

---

## TC-BROWSER — Cross-Browser

### TC-BROWSER-01: Core flows work on Safari
- **Steps:**
  1. Run TC-AUTH-01, TC-CUST-05, TC-ORDER-04, TC-BOOK-04 on Safari
- **Expected:** All pass without Safari-specific issues

### TC-BROWSER-02: Core flows work on Firefox
- **Steps:**
  1. Run TC-AUTH-01, TC-CUST-05, TC-ORDER-04, TC-BOOK-04 on Firefox
- **Expected:** All pass without Firefox-specific issues


---

## TC-AUTH Additional v2 — New Auth Flow

### TC-AUTH-09: Login returns temporary token indicator (not full access)
- **Steps:**
  1. Navigate to `/login`
  2. Enter valid email + password → submit
  3. Verify redirected to `/pin`
  4. Try navigating directly to `/customers`
- **Expected:** Redirected back to `/pin` — temporary token does not grant access to protected routes

### TC-AUTH-10: PIN verify completes authentication (JWT issued)
- **Precondition:** On `/pin` page after email+password login
- **Steps:**
  1. Enter correct PIN
  2. Submit
  3. Verify redirected to `/dashboard`
  4. Navigate to `/customers`
- **Expected:** `/customers` loads successfully — JWT now active after PIN

### TC-AUTH-11: Forgot password — request reset email
- **Steps:**
  1. Navigate to `/forgot-password`
  2. Enter registered email
  3. Submit
- **Expected:** `200` success message shown; no redirect to login (security: same response for unknown email)

### TC-AUTH-12: Forgot password — reset with valid token
- **Steps:**
  1. Navigate to `/reset-password?token=valid_token` (from email link)
  2. Enter new password + confirm
  3. Submit
- **Expected:** Success message; redirect to `/login`; can login with new password

### TC-AUTH-13: Change password while logged in
- **Steps:**
  1. Login as admin
  2. Navigate to `/settings`
  3. Click "Change Password"
  4. Enter old password + new password
  5. Submit
- **Expected:** Success toast; session remains active (no forced re-login)

