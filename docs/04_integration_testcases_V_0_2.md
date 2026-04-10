# Integration Test Cases — pytest
## Pila Studio Management

> **Framework:** pytest + httpx + Playwright (Python) for end-to-end flows
> **Coverage:** Full user journeys spanning FE ↔ BE ↔ Database
> **Date:** 2026-04-05
> **Strategy:** Run against a real test database (no mocks on the DB layer); use test-env email/LINE stubs

---

## Test Structure

```
tests/
  integration/
    test_auth_flow.py
    test_customer_lifecycle.py
    test_order_session_flow.py
    test_booking_flow.py
    test_role_access_flow.py
    test_permission_propagation.py
    test_data_consistency.py
    conftest.py        # real DB, seeded test data, full-stack fixtures
```

---

## Fixtures

```python
# full_stack_app    → spins up BE + DB in test mode
# browser_context   → Playwright browser per test
# seed_data         → inserts baseline: 3 branches, 1 owner, 1 admin/branch, 1 trainer/branch
# cleanup           → truncates tables after each test (or uses transactions rollback)
```

---

## TC-INT-AUTH — Authentication End-to-End

### TC-INT-AUTH-01: Complete login → PIN → dashboard flow
- **Steps:**
  1. Open browser, navigate to `/login`
  2. Enter valid email + password → submit
  3. Verify redirected to `/pin`
  4. Verify `GET /auth/me` returns 401 (PIN not yet verified)
  5. Enter correct PIN → submit
  6. Verify redirected to `/dashboard`
  7. Verify `GET /auth/me` returns 200 with user profile
- **Expected:** Full session established; dashboard data loads

### TC-INT-AUTH-02: PIN expiry re-prompt without full logout
- **Steps:**
  1. Login + PIN → dashboard
  2. Expire PIN session via API (set expiry to past)
  3. Navigate to `/customers`
  4. Verify redirect to `/pin` (not `/login`)
  5. Enter PIN again
  6. Verify redirected back to `/customers`
- **Expected:** Seamless PIN-only re-auth; no re-login required

### TC-INT-AUTH-03: Forgot PIN OTP flow — full cycle
- **Steps:**
  1. Login with email+password
  2. On `/pin`, click "Forgot PIN?"
  3. Check test-env email stub for OTP
  4. Enter OTP + new PIN
  5. Submit → redirected to `/pin`
  6. Enter new PIN → success
- **Expected:** PIN reset works; old PIN no longer valid

---

## TC-INT-CUST — Customer Lifecycle

### TC-INT-CUST-01: Create customer → verify in list → view detail
- **Steps:**
  1. Login as admin (Pattaya)
  2. POST `/customers` with valid payload (branch=Pattaya, source=MKT)
  3. GET `/customers` → verify customer appears with code `BPY-MKT001`
  4. GET `/customers/:id` → verify all fields match submitted data
  5. Navigate to `/customers` in browser → verify row appears
  6. Click customer row → verify detail page shows correct info
- **Expected:** DB record, API response, and UI all consistent

### TC-INT-CUST-02: Customer code running number — cross-branch isolation
- **Steps:**
  1. Create customer A: Pattaya, MKT → `BPY-MKT001`
  2. Create customer B: Kanchanaburi, MKT → `KAN-MKT001` (separate counter)
  3. Create customer C: Pattaya, MKT → `BPY-MKT002`
- **Expected:** Running numbers increment per branch+source independently

### TC-INT-CUST-03: Edit customer → changes reflected in UI
- **Steps:**
  1. Create customer via API
  2. PUT `/customers/:id` — change phone number
  3. Load customer detail in browser
- **Expected:** Updated phone number shown; no stale cache

### TC-INT-CUST-04: Delete customer → removed from list and all references
- **Steps:**
  1. Create customer + associated order
  2. DELETE `/customers/:id`
- **Expected:** Customer removed from list; order references show "Deleted customer" gracefully

### TC-INT-CUST-05: Admin cannot see customers from other branches
- **Steps:**
  1. Create customer in Kanchanaburi via owner API
  2. Login as Pattaya admin in browser
  3. Open `/customers`
- **Expected:** Kanchanaburi customer not visible in list

---

## TC-INT-ORDER — Order & Session Allocation Flow

### TC-INT-ORDER-01: Order creation → session balance allocation
- **Steps:**
  1. Create customer with 0 session balance
  2. Create package (10 hours)
  3. POST `/orders` — customer + package, 10 hours, 2 bonus hours
  4. GET `/sessions/remaining/:customer_id`
- **Expected:** `session_balance = 12` (10 + 2 bonus)

### TC-INT-ORDER-02: Session deduct → balance decrements → log created
- **Steps:**
  1. Create customer with session_balance = 5 (via order)
  2. POST `/sessions/deduct` → balance = 4
  3. GET `/sessions/log` — filter by customer
  4. GET `/sessions/remaining/:customer_id`
  5. Verify in browser: session log table shows new entry
- **Expected:**
  - DB: `session_balance = 4`
  - Log: type=DEDUCT, before=5, amount=1, after=4
  - UI: log row visible; remaining hours card updated

### TC-INT-ORDER-03: Cannot deduct when balance is zero
- **Steps:**
  1. Create customer, deduct all sessions (balance = 0)
  2. POST `/sessions/deduct` again
- **Expected:** `400 Bad Request` from API; browser shows error state if attempted via UI

### TC-INT-ORDER-04: Order with renew flag links to previous order
- **Steps:**
  1. Create initial order for customer
  2. Create second order with `renew: true`, referencing first order
  3. GET `/orders/:id` for second order
- **Expected:** Response includes `renewed_from_order_id` field pointing to first order

### TC-INT-ORDER-05: Outstanding balance visible on order list and detail
- **Steps:**
  1. Create order with total_price=5000, paid_amount=2000
  2. GET `/orders` → check `has_outstanding: true`
  3. Open order list in browser → check badge visible on row
- **Expected:** API flag and UI badge both present

---

## TC-INT-BOOK — Booking Flow

### TC-INT-BOOK-01: Full booking lifecycle — Pending → Confirmed → Notify
- **Steps:**
  1. Admin creates booking via POST `/bookings` (status=pending)
  2. Verify booking appears in timetable (amber color) in browser
  3. Admin confirms via PUT `/bookings/:id/confirm`
  4. Verify status = confirmed in DB
  5. Verify timetable slot changes to teal color in browser
  6. If customer has LINE → verify LINE notify prompt appears in browser
- **Expected:** Status transitions correct; UI reflects each state

### TC-INT-BOOK-02: Cancel booking by admin
- **Steps:**
  1. Create and confirm booking
  2. DELETE `/bookings/:id` as admin
  3. Verify slot cleared in timetable
  4. Verify status = cancelled in DB
- **Expected:** Booking removed from active view; audit trail preserved

### TC-INT-BOOK-03: Trainer can only schedule own slots
- **Steps:**
  1. Login as trainer A in browser
  2. Click empty slot
  3. Verify popup only allows selecting trainer A's name
  4. Try POST `/bookings` with trainer B's ID via API
- **Expected:** Browser: other trainer not selectable; API: 403 Forbidden

### TC-INT-BOOK-04: Multiple bookings per slot — no conflict blocking
- **Steps:**
  1. Create booking A at 10:00 (30min)
  2. Create booking B at 10:00 (different trainer)
  3. View timetable
- **Expected:** Both bookings visible in same slot (stacked); no conflict error

### TC-INT-BOOK-05: Booking session deduction upon class completion (future)
- **Note:** Placeholder — link from confirmed booking to session deduct TBD in sprint planning

---

## TC-INT-ROLE — Role-Based Access End-to-End

### TC-INT-ROLE-01: Developer can access all partners and branches
- **Steps:**
  1. Login as developer
  2. Navigate to `/customers` → data from all partners/branches visible
  3. Navigate to `/dashboard` → partner selector + branch selector visible
  4. Switch partner in selector → data changes to that partner's data
- **Expected:** Full cross-partner, cross-branch access confirmed

### TC-INT-ROLE-02: Owner can access all branches within own partner only
- **Steps:**
  1. Login as owner
  2. Navigate to `/customers?branch=pattaya` → data visible
  3. Navigate to `/customers?branch=kanchanaburi` → data visible
  4. Navigate to `/dashboard` → branch selector visible (no partner selector)
  5. Try `GET /customers` from another partner via API
- **Expected:** All branches within partner accessible; cross-partner API returns 403

### TC-INT-ROLE-03: Branch Master restricted to assigned branch — full feature access
- **Steps:**
  1. Login as branch_master (Pattaya)
  2. Navigate to `/customers` → only Pattaya customers visible
  3. Navigate to `/users` → can add users (admin/trainer only)
  4. Navigate to `/permissions` → can edit permission matrix
  5. Try `GET /customers?branch=kanchanaburi` via API
- **Expected:** Full feature access within branch; cross-branch data blocked

### TC-INT-ROLE-04: Admin restricted to permitted features in assigned branch
- **Steps:**
  1. Login as admin (Pattaya)
  2. Navigate to `/customers` → only Pattaya customers
  3. Try `GET /customers?branch=kanchanaburi` via API
  4. Try accessing `/users` (add user)
  5. Try accessing `/permissions`
- **Expected:** UI filtered to branch; user creation hidden/403; permissions page hidden/403

### TC-INT-ROLE-05: Trainer restricted to permitted features — own data by default
- **Steps:**
  1. Login as trainer A (Pattaya)
  2. Verify sidebar: no User/Permission/Branch Config menus
  3. Navigate to `/sessions/trainer-report` → only own training sessions visible
  4. Try `GET /dashboard?branch=all` via API
  5. Try `POST /sessions/deduct` (if trainer.session.deduct not permitted)
- **Expected:** Limited menu; own-data scoped; cross-branch API 403; unpermitted actions 403

### TC-INT-ROLE-06: Unauthenticated user cannot access any protected route
- **Steps:**
  1. Without logging in, try to navigate to `/customers`, `/orders`, `/dashboard`
  2. Try `GET /customers`, `GET /orders` without token
- **Expected:** UI: redirect to `/login`; API: 401 Unauthorized

### TC-INT-ROLE-07: Role hierarchy — lower role cannot create equal or higher role
- **Steps:**
  1. Login as branch_master
  2. Try `POST /users` with `role: "owner"`
  3. Try `POST /users` with `role: "branch_master"`
- **Expected:** Both return `403 Forbidden`; only `admin` and `trainer` creation allowed

---

## TC-INT-PERM — Permission Change Propagation

### TC-INT-PERM-01: Owner configures branch_master permissions → branch_master API affected
- **Steps:**
  1. Login as owner
  2. PUT `/permissions` — set `branch_master.booking.view = false`
  3. Login as branch_master → navigate to `/booking`
  4. Attempt `GET /bookings` via API with branch_master_token
- **Expected:** Browser shows "ฟีเจอร์นี้ไม่พร้อมใช้งาน" overlay; API returns 403

### TC-INT-PERM-01b: Owner configures admin permissions → admin blocked, branch_master unaffected
- **Steps:**
  1. Login as owner
  2. PUT `/permissions` — set `admin.booking.view = false`
  3. Login as admin → navigate to `/booking` → blocked
  4. Login as branch_master → navigate to `/booking` → still accessible
- **Expected:** Only the targeted role is affected; roles above it are not restricted

### TC-INT-PERM-01c: Branch_master configures admin/trainer — cannot touch owner permissions
- **Steps:**
  1. Login as branch_master
  2. PUT `/permissions` — set `trainer.order.view = false` → `200 OK`
  3. PUT `/permissions` — set `owner.order.view = false`
- **Expected:** Trainer permission update succeeds; owner permission update returns `403 Forbidden`

### TC-INT-PERM-02: Re-enabling permission restores access
- **Steps:**
  1. Disable booking for admin (from TC-INT-PERM-01b)
  2. PUT `/permissions` — set `admin.booking.view = true`
  3. Admin navigates to `/booking`
- **Expected:** Page loads normally; overlay gone

### TC-INT-PERM-03: Permission matrix columns match the logged-in role's hierarchy
- **Steps:**
  1. Login as developer → open `/permissions` → assert columns: owner, branch_master, admin, trainer
  2. Login as owner → open `/permissions` → assert columns: branch_master, admin, trainer
  3. Login as branch_master → open `/permissions` → assert columns: admin, trainer
  4. Login as admin → navigate to `/permissions`
- **Expected:** Each role sees only subordinate columns; admin gets 403/redirect

---

## TC-INT-DATA — Data Consistency

### TC-INT-DATA-01: Activity log created for all write operations
- **Steps:**
  1. Create customer → check activity log
  2. Edit customer → check activity log
  3. Create order → check activity log
  4. Deduct session → check activity log
  5. Confirm booking → check activity log
- **Expected:** Each action creates an activity log entry with correct actor, action, and target

### TC-INT-DATA-02: Session balance never goes negative
- **Steps:**
  1. Customer with balance=1
  2. Simultaneously send 2 concurrent POST `/sessions/deduct` requests
  3. Check final balance
- **Expected:** Balance = 0 (not -1); one deduction succeeds, second fails with 400

### TC-INT-DATA-03: Customer code uniqueness enforced at DB level
- **Steps:**
  1. Simultaneously POST 2 customers (same branch, same source type, rapid fire)
  2. Check generated codes
- **Expected:** Both codes unique; no duplicate codes in DB

### TC-INT-DATA-04: Order total consistency — session balance matches order history
- **Steps:**
  1. Create 3 orders for a customer (10h + 5h + 8h = 23h)
  2. Deduct 5 sessions
  3. GET `/sessions/remaining/:customer_id`
  4. Sum all order hours from GET `/orders?customer_id=...`
  5. Count session deductions from GET `/sessions/log?customer_id=...`
- **Expected:** remaining_balance == total_order_hours - total_deductions (= 23 - 5 = 18)

### TC-INT-DATA-05: Branch filter consistency — API and UI agree
- **Steps:**
  1. Seed: 10 customers Pattaya, 8 customers Kanchanaburi
  2. GET `/customers?branch=pattaya` → count = 10
  3. Login as Pattaya admin in browser → count visible = 10
  4. GET `/customers` as Pattaya admin → count = 10 (auto-filtered)
- **Expected:** API count, browser count, and role-scoped API count all consistent

---

## TC-INT-SETTINGS — Settings Propagation

### TC-INT-SET-01: Language preference saved per user
- **Steps:**
  1. Login as admin, set language to English
  2. Logout and login again
- **Expected:** Language is still English; preference persisted in DB

### TC-INT-SET-02: Dark mode preference saved per user
- **Steps:**
  1. Enable dark mode
  2. Logout and login again
- **Expected:** Dark mode still active

---

## Integration Test Execution Order

```
1. TC-INT-AUTH (pre-condition for all others)
2. TC-INT-ROLE (validates security layer)
3. TC-INT-PERM (validates permission system)
4. TC-INT-CUST (core entity lifecycle)
5. TC-INT-ORDER (depends on customers)
6. TC-INT-BOOK (depends on trainers + customers)
7. TC-INT-DATA (consistency checks across all)
8. TC-INT-SETTINGS (isolated, can run any time)
```

---

## TC-INT-LOGOUT — Logout Flow

### TC-INT-LOGOUT-01: Full logout flow — token invalidated
- **Steps:**
  1. Login + PIN → dashboard
  2. POST `/auth/logout`
  3. Try GET `/customers` with same token
  4. Navigate to `/customers` in browser
- **Expected:** API returns `401`; browser redirects to `/login`

---

## TC-INT-PAY — Payment Flow

### TC-INT-PAY-01: Full installment payment flow
- **Steps:**
  1. Create order: total=9000, paid=0
  2. POST `/orders/:id/payments` — amount=3000 (งวด 1)
  3. GET `/orders/:id/payments` → outstanding=6000
  4. POST `/orders/:id/payments` — amount=3000 (งวด 2)
  5. GET `/orders/:id/payments` → outstanding=3000
  6. POST `/orders/:id/payments` — amount=3000 (งวด 3)
  7. GET `/orders/:id` → outstanding=0
  8. Open order detail in browser
- **Expected:** Payment breakdown shows fully paid; outstanding badge disappears from order list

### TC-INT-PAY-02: Receipt email sent after order creation
- **Steps:**
  1. Create order via POST `/orders`
  2. POST `/orders/:id/receipt`
  3. Check mock email inbox
- **Expected:** Email received with correct order details (customer name, package, hours, total price)

---

## TC-INT-PRINT — Signature Print Flow

### TC-INT-PRINT-01: Full Google Drive generate flow
- **Steps:**
  1. Connect Google Account via POST `/settings/google/connect` (mock OAuth)
  2. GET `/settings/google/storage` → note initial usage
  3. POST `/signature-print/generate` with valid order_id
  4. Verify `file_url` returned
  5. GET `/signature-print/list` → file appears
  6. GET `/settings/google/storage` → usage increased
  7. Navigate to `/signature-print` in browser → link visible and clickable
- **Expected:** File created in Drive; link accessible; storage updated in UI

### TC-INT-PRINT-02: Storage warning shown when Drive near full
- **Steps:**
  1. Mock Google Drive API to return storage at 95% full
  2. Navigate to `/signature-print` in browser
- **Expected:** Warning banner visible; generate button still available but warned

---

## TC-INT-CARE — Caretaker Flow

### TC-INT-CARE-01: Create caretaker → assign to customer → autofill in order
- **Steps:**
  1. POST `/caretakers` — create "เตย" for Pattaya branch
  2. POST `/customers` — assign caretaker_id = เตย
  3. In browser: open new order form → select that customer
  4. Verify caretaker field autofills with "เตย"
  5. GET `/orders/:id` after save → caretaker_id matches
- **Expected:** Caretaker flows from creation → customer profile → order autofill → DB record

### TC-INT-CARE-02: Admin sees only own branch caretakers in all forms
- **Steps:**
  1. Create caretaker A in Pattaya, caretaker B in Kanchanaburi
  2. Login as Pattaya admin in browser
  3. Open customer form → caretaker selector
  4. Open order form → caretaker selector
- **Expected:** Only caretaker A (Pattaya) visible in both forms; B not shown

---

## TC-INT-CANCEL — Cancel Booking Flow

### TC-INT-CANCEL-01: Cancel booking — session returned (policy = return)
- **Steps:**
  1. PUT `/settings/cancel-policy` — `{ return_session: true }`
  2. Create order → session_balance = 10
  3. Create + confirm booking
  4. GET `/sessions/remaining/:customer_id` → balance = 10
  5. DELETE `/bookings/:id` (cancel)
  6. GET `/sessions/remaining/:customer_id`
  7. GET `/sessions/log` → check new entry
  8. View session log in browser
- **Expected:** balance = 11; log entry type=ADJUST; UI shows updated balance

### TC-INT-CANCEL-02: Cancel booking — session NOT returned (policy = no return)
- **Steps:**
  1. PUT `/settings/cancel-policy` — `{ return_session: false }`
  2. Create order → session_balance = 10
  3. Create + confirm booking
  4. DELETE `/bookings/:id`
  5. GET `/sessions/remaining/:customer_id`
- **Expected:** balance = 10 (unchanged); no ADJUST log entry

### TC-INT-CANCEL-03: Cancel policy hours_before enforced
- **Steps:**
  1. PUT `/settings/cancel-policy` — `{ hours_before: 24 }`
  2. Create booking starting in 12 hours
  3. DELETE `/bookings/:id`
- **Expected:** `400 Bad Request` — `{ "detail": "Cannot cancel within 24 hours of booking" }`

---

## TC-INT-EXTBOOK — External API Booking Flow

### TC-INT-EXTBOOK-01: External pending → admin confirm → notify LINE
- **Steps:**
  1. POST `/bookings/external` (external API key) — creates pending booking
  2. Login as admin in browser → navigate to `/booking`
  3. Verify pending slot shows amber color
  4. Admin clicks confirm → PUT `/bookings/:id/confirm`
  5. Verify slot turns teal
  6. Customer has LINE registered → verify "Notify customer?" prompt appears
  7. Admin clicks Yes → LINE notification sent (mock)
- **Expected:** Full flow works; status transitions correct; UI reflects each state

### TC-INT-EXTBOOK-02: External booking — non-contiguous slots rejected
- **Steps:**
  1. POST `/bookings/external` with non-contiguous slots
- **Expected:** `400 Bad Request`; no pending booking created; timetable unchanged

### TC-INT-EXTBOOK-03: External booking — customer can only book own branch
- **Steps:**
  1. POST `/bookings/external` with branch_id from different branch than customer's
- **Expected:** `403 Forbidden`

---

## TC-INT-BRANCH — Branch Config Flow

### TC-INT-BRANCH-01: Create branch → customer code uses new prefix
- **Steps:**
  1. POST `/branches` — `{ name: "Bangkok", prefix: "BKK", source_types: [{label: "Page", code: "MKT"}] }`
  2. POST `/customers` — branch=Bangkok, source=Page
  3. GET `/customers/:id`
  4. View customer list in browser
- **Expected:** Customer code = `BKK-MKT001`; appears correctly in browser

### TC-INT-BRANCH-02: Edit source type → new customers use updated code
- **Steps:**
  1. PUT `/branches/:id` — change source type code from "PAT" to "PTY"
  2. POST `/customers` — branch=Pattaya, source=Walk In
  3. GET `/customers/:id`
- **Expected:** New code uses "PTY" not "PAT"; existing customers unaffected

### TC-INT-BRANCH-03: Edit opening hours → timetable reflects change
- **Steps:**
  1. PUT `/branches/:id` — opening_time="10:00", closing_time="20:00"
  2. Navigate to `/booking` in browser
- **Expected:** Timetable starts at 10:00 and ends at 20:00 for that branch

---

## TC-INT-PKG — Package Scope Flow

### TC-INT-PKG-01: Selected branch package — only visible in correct branch
- **Steps:**
  1. POST `/packages` — `{ branch_scope: "selected", branch_ids: ["pattaya_id"] }`
  2. Login as Pattaya admin → open order form → package chip
  3. Login as Kanchanaburi admin → open order form → package chip
- **Expected:** Package visible for Pattaya; NOT visible for Kanchanaburi

### TC-INT-PKG-02: Package active period — only active during range
- **Steps:**
  1. POST `/packages` — active_from=yesterday, active_until=tomorrow
  2. GET `/packages?active_only=true` → package included
  3. Mock date to day after tomorrow
  4. GET `/packages?active_only=true` → package excluded
  5. Open order form in browser → package not available
- **Expected:** Package availability changes with time; UI reflects correctly

---

## TC-INT-SESS-ADJ — Session Adjust Flow

### TC-INT-SESS-ADJ-01: Manual adjust → balance updated → log created → UI reflects
- **Steps:**
  1. Customer session_balance = 5
  2. PUT `/sessions/adjust` — `{ adjustment: 3, reason: "bonus" }`
  3. GET `/sessions/remaining/:customer_id` → balance = 8
  4. GET `/sessions/log` → entry type=ADJUST, before=5, amount=3, after=8
  5. GET `/activity-log` → entry action="session.adjust"
  6. Navigate to session log in browser → new row visible
- **Expected:** Balance, session log, activity log, and UI all consistent

---

## TC-INT-HELP — Help Page Flow

### TC-INT-HELP-01: Role-specific manual — trainer sees limited content
- **Steps:**
  1. Login as trainer in browser
  2. Navigate to `/help`
  3. GET `/help/manual` with trainer token via API
- **Expected:** Manual shows only trainer-relevant sections; no order/user management sections

### TC-INT-HELP-02: Branch QR matches user's branch
- **Steps:**
  1. Login as Kanchanaburi admin
  2. GET `/help/line-qr`
  3. Navigate to `/help` in browser
- **Expected:** API returns Kanchanaburi branch QR; browser displays correct QR

---

## TC-INT-CONCURRENT — Concurrent Operations

### TC-INT-CON-01: Concurrent order creation — session balance correct
- **Steps:**
  1. Customer session_balance = 0
  2. Simultaneously POST 2 orders (10h each) for same customer
  3. GET `/sessions/remaining/:customer_id`
- **Expected:** balance = 20 (both orders processed correctly; no race condition)

### TC-INT-CON-02: Concurrent booking confirm — no double confirm
- **Steps:**
  1. Create pending booking
  2. Simultaneously send 2 PUT `/bookings/:id/confirm`
- **Expected:** One returns `200 OK`; one returns `409 Conflict` or `400`; status = confirmed once

---

## TC-INT-TOGGLE — Feature Toggle Live Propagation

### TC-INT-TOGGLE-01: Feature toggle off → active sessions blocked immediately
- **Steps:**
  1. Admin logged in with active session — Booking page accessible
  2. Owner disables Booking module via PUT `/permissions` (feature toggle)
  3. Admin tries GET `/bookings` without re-login
  4. Admin navigates to `/booking` in browser without re-login
- **Expected:** API returns `403` immediately; browser shows overlay without needing re-login

### TC-INT-TOGGLE-02: Re-enable feature → access restored immediately
- **Steps:**
  1. Booking disabled for admin (from TC-INT-TOGGLE-01)
  2. Owner re-enables Booking
  3. Admin tries GET `/bookings` without re-login
- **Expected:** `200 OK` immediately; overlay gone in browser

---

## TC-INT-LOG-CONSISTENCY — Activity Log Consistency

### TC-INT-LOG-01: All write operations create activity log entries
- **Steps:**
  1. POST `/customers` → check log: action="customer.create"
  2. PUT `/customers/:id` → check log: action="customer.edit"
  3. DELETE `/customers/:id` → check log: action="customer.delete"
  4. POST `/orders` → check log: action="order.create"
  5. PUT `/bookings/:id/confirm` → check log: action="booking.confirm"
  6. DELETE `/bookings/:id` → check log: action="booking.cancel"
  7. PUT `/sessions/adjust` → check log: action="session.adjust"
  8. POST `/users` → check log: action="user.create"
  9. PUT `/permissions` → check log: action="permission.update"
- **Expected:** Every write operation has corresponding activity log entry with correct actor, action, branch

### TC-INT-LOG-02: Cancel booking with session return — both logs consistent
- **Steps:**
  1. Cancel booking (policy = return)
  2. GET `/activity-log` → check booking.cancel entry
  3. GET `/sessions/log` → check ADJUST entry
- **Expected:** Both logs exist; timestamps close; actor same; session balance consistent

