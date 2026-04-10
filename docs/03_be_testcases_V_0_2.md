# BE Test Cases — pytest
## Pila Studio Management

> **Framework:** pytest + httpx (async HTTP client)
> **Coverage:** All API endpoints, auth, role guards, data validation, business rules
> **Date:** 2026-04-05

---

## Test Structure

```
tests/
  be/
    test_auth_api.py
    test_customer_api.py
    test_order_api.py
    test_customer_hour_api.py
    test_trainer_api.py
    test_package_api.py
    test_booking_api.py
    test_user_api.py
    test_permission_api.py
    test_dashboard_api.py
    test_activity_log_api.py
    conftest.py          # fixtures: test DB, auth tokens per role, factory helpers
```

---

## Fixtures (conftest.py)

```python
# auth_token(role)        → returns JWT for: developer | owner | branch_master | admin | trainer
# developer_token         → shorthand fixture — full access, all partners/branches
# owner_token             → shorthand fixture — full access within partner
# branch_master_token     → shorthand fixture — full access within assigned branch
# admin_token             → shorthand fixture — permission-matrix-gated, assigned branch
# trainer_token           → shorthand fixture — permission-matrix-gated, assigned branch
# create_customer()       → factory: inserts test customer, returns id
# create_order()          → factory: inserts test order, returns id
# create_trainer()        → factory: inserts test trainer, returns id
# create_package()        → factory: inserts test package, returns id
# db_session              → SQLAlchemy session (rolls back after each test)
```

---

## TC-API-AUTH — Authentication API

### TC-API-AUTH-01: POST /auth/login — valid credentials
- **Input:** `{ "email": "owner@test.com", "password": "valid_pass" }`
- **Expected:** `200 OK` — `{ "access_token": "...", "token_type": "bearer" }`

### TC-API-AUTH-02: POST /auth/login — wrong password
- **Input:** `{ "email": "owner@test.com", "password": "wrong" }`
- **Expected:** `401 Unauthorized` — `{ "detail": "Invalid credentials" }`

### TC-API-AUTH-03: POST /auth/login — unknown email
- **Input:** `{ "email": "nobody@test.com", "password": "pass" }`
- **Expected:** `401 Unauthorized`

### TC-API-AUTH-04: POST /auth/pin/verify — valid PIN
- **Precondition:** Login token obtained
- **Input:** `{ "pin": "123456" }`
- **Expected:** `200 OK` — PIN session established; full access token returned

### TC-API-AUTH-05: POST /auth/pin/verify — wrong PIN
- **Input:** `{ "pin": "000000" }`
- **Expected:** `401 Unauthorized` — `{ "detail": "Invalid PIN" }`

### TC-API-AUTH-06: POST /auth/pin/forgot — valid email
- **Input:** `{ "email": "owner@test.com" }`
- **Expected:** `200 OK` — OTP sent (check mock email in test env)

### TC-API-AUTH-07: POST /auth/pin/reset — valid OTP
- **Input:** `{ "otp": "654321", "new_pin": "999999" }`
- **Expected:** `200 OK` — PIN updated

### TC-API-AUTH-08: POST /auth/pin/reset — expired OTP
- **Input:** `{ "otp": "expired_otp", "new_pin": "999999" }`
- **Expected:** `400 Bad Request` — `{ "detail": "OTP expired or invalid" }`

### TC-API-AUTH-09: Protected route without token
- **Input:** `GET /customers` — no Authorization header
- **Expected:** `401 Unauthorized`

### TC-API-AUTH-10: Protected route with expired token
- **Input:** `GET /customers` with expired JWT
- **Expected:** `401 Unauthorized`

---

## TC-API-CUST — Customer API

### TC-API-CUST-01: GET /customers — returns paginated list
- **Auth:** admin_token
- **Expected:** `200 OK` — `{ "items": [...], "total": N, "page": 1 }`
- **Assert:** No UUID values in `name`, `nickname`, `trainer_name` fields

### TC-API-CUST-02: GET /customers — admin sees only own branch
- **Auth:** admin_token (Pattaya branch)
- **Expected:** All returned customers belong to Pattaya branch only

### TC-API-CUST-02b: GET /customers — trainer sees only own branch
- **Auth:** trainer_token (Pattaya branch)
- **Expected:** All returned customers belong to Pattaya branch only

### TC-API-CUST-02c: GET /customers — branch_master sees only assigned branch
- **Auth:** branch_master_token (Pattaya branch)
- **Expected:** All returned customers belong to Pattaya branch only

### TC-API-CUST-03: GET /customers — owner sees all branches within partner
- **Auth:** owner_token
- **Expected:** Customers from all 3 branches (within partner) returned

### TC-API-CUST-03b: GET /customers — developer sees all branches across all partners
- **Auth:** developer_token
- **Expected:** Customers from all partners and branches returned

### TC-API-CUST-04: GET /customers?search=นาม — filters by name
- **Expected:** Only customers matching "นาม" in name/nickname returned

### TC-API-CUST-05: GET /customers?branch=pattaya&status=active
- **Expected:** Only active Pattaya customers returned

### TC-API-CUST-06: POST /customers — create valid customer
- **Auth:** admin_token
- **Input:** Full valid customer payload
- **Expected:** `201 Created` — customer returned with auto-generated code matching `BPY-[SOURCE][N]` pattern

### TC-API-CUST-07: POST /customers — customer code auto-increment
- **Steps:**
  1. Create customer A (Pattaya, MKT source) → code = `BPY-MKT001`
  2. Create customer B (Pattaya, MKT source) → code = `BPY-MKT002`
- **Expected:** Running numbers increment correctly per branch+source

### TC-API-CUST-08: POST /customers — missing required field
- **Input:** Payload missing `first_name`
- **Expected:** `422 Unprocessable Entity` — validation error detail

### TC-API-CUST-09: POST /customers — trainer not in selected branch
- **Input:** Customer in Pattaya branch with trainer_id from Kanchanaburi
- **Expected:** `400 Bad Request` — `{ "detail": "Trainer does not belong to selected branch" }`

### TC-API-CUST-10: GET /customers/:id — returns full detail
- **Expected:** All fields + order_history list + session_remaining

### TC-API-CUST-11: GET /customers/:id — 404 for unknown id
- **Expected:** `404 Not Found`

### TC-API-CUST-12: PUT /customers/:id — updates correctly
- **Input:** Updated phone number
- **Expected:** `200 OK` — updated customer returned

### TC-API-CUST-13: DELETE /customers/:id — owner can delete within partner
- **Auth:** owner_token
- **Expected:** `204 No Content`

### TC-API-CUST-13b: DELETE /customers/:id — branch_master can delete within branch
- **Auth:** branch_master_token
- **Expected:** `204 No Content`

### TC-API-CUST-14: DELETE /customers/:id — trainer cannot delete
- **Auth:** trainer_token
- **Expected:** `403 Forbidden`

### TC-API-CUST-14b: DELETE /customers/:id — admin blocked if permission matrix disallows
- **Auth:** admin_token (customer.delete = false in matrix)
- **Expected:** `403 Forbidden`

---

## TC-API-ORDER — Order API

### TC-API-ORDER-01: GET /orders — returns list with pagination
- **Auth:** admin_token
- **Expected:** `200 OK` — paginated orders for admin's branch

### TC-API-ORDER-02: GET /orders?start_date=&end_date= — date filter
- **Expected:** Only orders within date range returned

### TC-API-ORDER-03: GET /orders — outstanding_balance flag on relevant orders
- **Expected:** Orders with unpaid amount have `has_outstanding: true`

### TC-API-ORDER-04: POST /orders — valid order creates and allocates sessions
- **Auth:** admin_token
- **Input:** Valid order (customer_id, package_id, hours, payment_method, total_price)
- **Expected:**
  - `201 Created`
  - Customer's `hour_balance` incremented by `hours + bonus_hours`
  - Activity log entry created

### TC-API-ORDER-05: POST /orders — package not active
- **Input:** `package_id` pointing to expired package
- **Expected:** `400 Bad Request` — `{ "detail": "Package is not active" }`

### TC-API-ORDER-06: POST /orders — package wrong branch
- **Input:** Package scoped to Kanchanaburi for a Pattaya order
- **Expected:** `400 Bad Request` — `{ "detail": "Package not available for this branch" }`

### TC-API-ORDER-07: POST /orders — missing required fields
- **Expected:** `422 Unprocessable Entity`

### TC-API-ORDER-08: GET /orders/:id — returns detail with payment breakdown
- **Expected:** Includes `payment_method`, `total_price`, `paid_amount`, `outstanding`, `installments[]`

### TC-API-ORDER-09: PUT /orders/:id — update order notes
- **Expected:** `200 OK`

### TC-API-ORDER-10: Trainer cannot create order (default permission)
- **Auth:** trainer_token
- **Expected:** `403 Forbidden`

### TC-API-ORDER-10b: Admin blocked if permission matrix disallows order.create
- **Auth:** admin_token (order.create = false in matrix)
- **Expected:** `403 Forbidden`

---

## TC-API-HOUR — Customer Hour API

### TC-API-HOUR-01: POST /customer-hours/deduct — valid deduction
- **Auth:** admin_token
- **Input:** `{ "customer_id": "...", "branch_id": "..." }`
- **Expected:**
  - `200 OK`
  - `hour_balance` decremented by 1
  - Transaction log entry: type=HOUR_DEDUCT, before=N, amount=1, after=N-1

### TC-API-HOUR-02: POST /customer-hours/deduct — zero balance
- **Input:** Customer with `hour_balance = 0`
- **Expected:** `400 Bad Request` — `{ "detail": "No remaining hours" }`

### TC-API-HOUR-03: GET /customer-hours/log — returns transaction history
- **Expected:** List with fields: timestamp, customer_code, customer_name, transaction_type, before, amount, after, user_id
- **Assert:** No UUIDs exposed as display values

### TC-API-HOUR-04: GET /customer-hours/log?customer_id=&start_date= — filters work
- **Expected:** Only matching transactions returned

### TC-API-HOUR-05: GET /customer-hours/trainer-report — returns summary
- **Auth:** admin_token
- **Params:** `trainer_id=..., start_date=..., end_date=...`
- **Expected:** `{ "total_hours": N, "session_count": N, "history": [...] }`

### TC-API-HOUR-06: GET /customer-hours/remaining/:customer_id — returns balance
- **Expected:** `{ "customer_id": "...", "hour_balance": N, "last_updated": "..." }`

### TC-API-HOUR-07: Master can only view own deductions
- **Auth:** master_token
- **Steps:** Request trainer report for a different trainer
- **Expected:** `403 Forbidden`

---

## TC-API-TRAINER — Trainer API

### TC-API-TRAINER-01: GET /trainers — returns list filtered by branch for admin
- **Auth:** admin_token (Pattaya)
- **Expected:** Only Pattaya trainers returned

### TC-API-TRAINER-02: POST /trainers — create valid trainer
- **Auth:** admin_token
- **Input:** `{ "name": "...", "email": "...", "branch_id": "...", "status": "ACTIVE" }`
- **Expected:** `201 Created`

### TC-API-TRAINER-03: DELETE /trainers/:id — fail if trainer has active customers
- **Expected:** `409 Conflict` — `{ "detail": "Trainer has active customers assigned" }`

---

## TC-API-PKG — Package API

### TC-API-PKG-01: GET /packages — returns list with status
- **Expected:** Each package includes computed `status` (active/inactive/expired) based on active_period dates

### TC-API-PKG-02: POST /packages — create valid package
- **Input:** `{ "name": "...", "hours": 10, "type": "SALE", "price": 5000, "branch_scope": "ALL" }`
- **Expected:** `201 Created`

### TC-API-PKG-03: GET /packages?active_only=true — only active packages
- **Expected:** No expired or inactive packages in response

### TC-API-PKG-04: Package status computed correctly
- **Steps:**
  1. Create package with `active_until` = yesterday
  2. GET /packages
- **Expected:** Package has `status: "expired"`

---

## TC-API-USER — User Management API

### TC-API-USER-01: GET /users — developer sees all users across all partners
- **Auth:** developer_token
- **Expected:** Users from all partners and branches

### TC-API-USER-01b: GET /users — owner sees all users within partner
- **Auth:** owner_token
- **Expected:** Users from all branches within the partner only

### TC-API-USER-01c: GET /users — branch_master sees only own branch users
- **Auth:** branch_master_token (Pattaya)
- **Expected:** Only Pattaya users returned

### TC-API-USER-02: POST /users — owner creates branch_master in own partner
- **Auth:** owner_token
- **Input:** `{ ..., "role": "BRANCH_MASTER", "branch_id": "pattaya_id" }`
- **Expected:** `201 Created`

### TC-API-USER-02b: POST /users — branch_master creates admin in own branch
- **Auth:** branch_master_token (Pattaya)
- **Input:** `{ ..., "role": "ADMIN", "branch_id": "pattaya_id" }`
- **Expected:** `201 Created`

### TC-API-USER-02c: POST /users — branch_master creates trainer in own branch
- **Auth:** branch_master_token (Pattaya)
- **Input:** `{ ..., "role": "TRAINER", "branch_id": "pattaya_id" }`
- **Expected:** `201 Created`

### TC-API-USER-03: POST /users — branch_master cannot create user for other branch
- **Auth:** branch_master_token (Pattaya)
- **Input:** `{ ..., "branch_id": "kanchanaburi_id" }`
- **Expected:** `403 Forbidden`

### TC-API-USER-03b: POST /users — branch_master cannot create owner or branch_master role
- **Auth:** branch_master_token
- **Input:** `{ ..., "role": "OWNER" }`
- **Expected:** `403 Forbidden` — cannot create equal or higher role

### TC-API-USER-03c: POST /users — admin cannot create any user
- **Auth:** admin_token
- **Expected:** `403 Forbidden`

### TC-API-USER-04: POST /users — password stored as hash
- **Steps:**
  1. Create user with password "plaintext"
  2. Query DB directly
- **Expected:** `password_hash` column is bcrypt hash, NOT "plaintext"

### TC-API-USER-05: PUT /users/:id/role — only owner or developer can change roles
- **Auth:** admin_token
- **Expected:** `403 Forbidden`

### TC-API-USER-05b: PUT /users/:id/role — branch_master cannot elevate to owner
- **Auth:** branch_master_token
- **Input:** `{ "role": "OWNER" }`
- **Expected:** `403 Forbidden`

---

## TC-API-PERM — Permission API

### TC-API-PERM-01: GET /permissions — developer sees all 4 role columns
- **Auth:** developer_token
- **Expected:** Matrix keys: `owner`, `branch_master`, `admin`, `trainer`

### TC-API-PERM-01b: GET /permissions — owner sees 3 role columns (below owner)
- **Auth:** owner_token
- **Expected:** Matrix keys: `branch_master`, `admin`, `trainer`
- **Assert:** No `developer` or `owner` key in response

### TC-API-PERM-01c: GET /permissions — branch_master sees 2 role columns (below branch_master)
- **Auth:** branch_master_token
- **Expected:** Matrix keys: `admin`, `trainer`
- **Assert:** No `developer`, `owner`, or `branch_master` key in response

### TC-API-PERM-01d: GET /permissions — admin and trainer have no access
- **Auth:** admin_token
- **Expected:** `403 Forbidden`
- **Auth:** trainer_token
- **Expected:** `403 Forbidden`

### TC-API-PERM-02: PUT /permissions — developer can update any role's permissions
- **Auth:** developer_token
- **Input:** Toggle `owner.branch_config.edit = false`
- **Expected:** `200 OK` — change persisted

### TC-API-PERM-02b: PUT /permissions — owner can update branch_master/admin/trainer permissions
- **Auth:** owner_token
- **Input:** Toggle `admin.package.view = false`
- **Expected:** `200 OK` — change persisted

### TC-API-PERM-02c: PUT /permissions — owner cannot update developer permissions
- **Auth:** owner_token
- **Input:** Toggle `developer.some_feature = false`
- **Expected:** `403 Forbidden` — cannot configure roles above or equal to own role

### TC-API-PERM-02d: PUT /permissions — branch_master can update admin/trainer permissions
- **Auth:** branch_master_token
- **Input:** Toggle `trainer.order.create = true`
- **Expected:** `200 OK` — change persisted for that branch

### TC-API-PERM-02e: PUT /permissions — branch_master cannot update owner permissions
- **Auth:** branch_master_token
- **Input:** Toggle `owner.user.create = false`
- **Expected:** `403 Forbidden`

### TC-API-PERM-03: PUT /permissions — admin cannot update any permissions
- **Auth:** admin_token
- **Expected:** `403 Forbidden`

### TC-API-PERM-03b: PUT /permissions — trainer cannot update any permissions
- **Auth:** trainer_token
- **Expected:** `403 Forbidden`

### TC-API-PERM-04: Permission guard — disabled module returns 403
- **Steps:**
  1. Owner disables booking module via PUT /permissions (feature toggle)
  2. Admin calls GET /bookings
- **Expected:** `403 Forbidden` — `{ "detail": "Module not enabled" }`

---

## TC-API-DASH — Dashboard API

### TC-API-DASH-01: GET /dashboard — trainer sees own data only
- **Auth:** master_token
- **Expected:** Stats scoped to this trainer only

### TC-API-DASH-02: GET /dashboard — admin sees branch data
- **Auth:** admin_token (Pattaya)
- **Expected:** Stats scoped to Pattaya branch

### TC-API-DASH-03: GET /dashboard?range=today
- **Expected:** Only today's data in stat cards

### TC-API-DASH-04: GET /dashboard?branch=all — owner sees all branches in partner
- **Auth:** owner_token
- **Expected:** Cross-branch aggregate data within partner returned

### TC-API-DASH-04b: GET /dashboard?partner=all — developer sees all partners
- **Auth:** developer_token
- **Expected:** Cross-partner aggregate data returned

### TC-API-DASH-05: GET /dashboard?branch=all — admin forbidden
- **Auth:** admin_token
- **Expected:** `403 Forbidden`

### TC-API-DASH-05b: GET /dashboard?branch=all — trainer forbidden
- **Auth:** trainer_token
- **Expected:** `403 Forbidden`

---

## TC-API-BOOK — Booking API

### TC-API-BOOK-01: GET /bookings — returns timetable slots
- **Expected:** Slots with status (pending/confirmed/cancelled), trainer, customer

### TC-API-BOOK-02: POST /bookings — admin creates booking
- **Auth:** admin_token
- **Input:** `{ "customer_id": "...", "trainer_id": "...", "start_time": "...", "duration_minutes": 60 }`
- **Expected:** `201 Created` — status = "pending"

### TC-API-BOOK-03: POST /bookings — trainer schedules own slot
- **Auth:** master_token
- **Input:** `{ "trainer_id": "<own_id>", ... }`
- **Expected:** `201 Created`

### TC-API-BOOK-04: POST /bookings — trainer cannot book for another trainer
- **Auth:** master_token
- **Input:** `{ "trainer_id": "<other_trainer_id>", ... }`
- **Expected:** `403 Forbidden`

### TC-API-BOOK-05: PUT /bookings/:id/confirm — confirm pending booking
- **Auth:** admin_token
- **Expected:** `200 OK` — status = "confirmed"; LINE notify flag returned if customer has LINE

### TC-API-BOOK-06: DELETE /bookings/:id — cancel booking (admin+)
- **Auth:** admin_token
- **Expected:** `200 OK` — status = "cancelled"

### TC-API-BOOK-07: DELETE /bookings/:id — master cannot cancel
- **Auth:** master_token
- **Expected:** `403 Forbidden`

---

## TC-API-LOG — Activity Log API

### TC-API-LOG-01: GET /activity-log — returns entries
- **Auth:** owner_token
- **Expected:** Entries with: timestamp, user_id, action, target_type, target_id, changes

### TC-API-LOG-02: GET /activity-log?user_id=&action_type= — filters work
- **Expected:** Only matching logs

### TC-API-LOG-03: Activity log entry created on customer create
- **Steps:**
  1. POST /customers (valid payload)
  2. GET /activity-log
- **Expected:** New entry with action="customer.create"

### TC-API-LOG-04: Activity log entry created on session deduct
- **Steps:**
  1. POST /customer-hours/deduct
  2. GET /activity-log
- **Expected:** New entry with action="customer_hour.deduct"

---

## TC-API-BRANCH — Branch Config API

### TC-API-BRANCH-01: GET /branches — returns all branches
- **Expected:** List with: name, prefix, source_types[], operating_hours

### TC-API-BRANCH-02: PUT /branches/:id — owner can update
- **Auth:** owner_token
- **Expected:** `200 OK`

### TC-API-BRANCH-03: PUT /branches/:id — admin cannot update
- **Auth:** admin_token
- **Expected:** `403 Forbidden`

---

## TC-API-AUTH Additional

### TC-API-AUTH-11: POST /auth/logout — invalidate token
- **Auth:** any valid token
- **Input:** valid Authorization header
- **Expected:** `200 OK` — token invalidated; subsequent requests with same token return `401`

### TC-API-AUTH-12: PIN lockout after N wrong attempts
- **Auth:** login token obtained
- **Input:** wrong PIN submitted 5 times consecutively
- **Expected:** `423 Locked` — `{ "detail": "PIN locked. Please reset via OTP" }`

### TC-API-AUTH-13: OTP rate limit — request too frequently
- **Input:** POST /auth/pin/forgot called 3 times within 60 seconds
- **Expected:** `429 Too Many Requests` — `{ "detail": "Too many OTP requests. Try again later" }`

### TC-API-AUTH-14: Login brute force protection
- **Input:** POST /auth/login with wrong password 10 times
- **Expected:** `429 Too Many Requests` after threshold

### TC-API-AUTH-15: Token cannot be used across partners
- **Auth:** owner_token from Partner A
- **Input:** GET /customers with Partner B's branch_id
- **Expected:** `403 Forbidden`

---

## TC-API-CUST Additional

### TC-API-CUST-15: GET /customers — pagination page 2
- **Auth:** owner_token
- **Params:** `?page=2&page_size=10`
- **Expected:** `200 OK` — `{ items: [...], total: N, page: 2, page_size: 10 }` — items are second set

### TC-API-CUST-16: GET /customers — page size limit enforced
- **Params:** `?page_size=999`
- **Expected:** `400 Bad Request` — max page size enforced (e.g. 100)

### TC-API-CUST-17: POST /customers — invalid email format
- **Input:** `{ "email": "not-an-email" }`
- **Expected:** `422 Unprocessable Entity`

### TC-API-CUST-18: POST /customers — name exceeds max length
- **Input:** `{ "first_name": "A" * 300 }`
- **Expected:** `422 Unprocessable Entity`

### TC-API-CUST-19: POST /customers — concurrent duplicate code race condition
- **Steps:**
  1. Simultaneously POST 2 customers (same branch, same source type)
- **Expected:** Both codes unique; no duplicate in DB; one may retry

---

## TC-API-ORDER Additional

### TC-API-ORDER-11: POST /orders/:id/payments — record installment payment
- **Auth:** admin_token
- **Input:** `{ "amount": 1000, "paid_at": "2026-04-05", "note": "งวด 1" }`
- **Expected:** `201 Created` — outstanding balance decremented correctly

### TC-API-ORDER-12: GET /orders/:id/payments — installment history
- **Auth:** admin_token
- **Expected:** `200 OK` — list of payments with: amount, paid_at, note, remaining_balance

### TC-API-ORDER-13: POST /orders/:id/receipt — send receipt email
- **Auth:** admin_token
- **Expected:** `200 OK` — email sent to customer email (check mock inbox in test env)

### TC-API-ORDER-14: POST /orders — hours field cannot be negative
- **Input:** `{ "hours": -5 }`
- **Expected:** `422 Unprocessable Entity`

### TC-API-ORDER-15: POST /orders — price field cannot be negative
- **Input:** `{ "total_price": -1000 }`
- **Expected:** `422 Unprocessable Entity`

### TC-API-ORDER-16: POST /orders — package before active period blocked
- **Input:** package with `active_from` = tomorrow
- **Expected:** `400 Bad Request` — `{ "detail": "Package is not yet active" }`

---

## TC-API-HOUR Additional

### TC-API-HOUR-08: PUT /customer-hours/adjust — manual adjust session balance (positive)
- **Auth:** admin_token
- **Input:** `{ "customer_id": "...", "adjustment": 5, "reason": "manual correction" }`
- **Expected:**
  - `200 OK`
  - `hour_balance` updated correctly
  - Transaction log: type=HOUR_ADJUST, before=N, amount=5, after=N+5

### TC-API-HOUR-09: PUT /customer-hours/adjust — negative adjustment reduces balance
- **Input:** `{ "adjustment": -3 }`
- **Expected:** `200 OK` — balance decremented by 3; log entry created

### TC-API-HOUR-10: PUT /customer-hours/adjust — cannot adjust below zero
- **Input:** customer balance=2, adjustment=-5
- **Expected:** `400 Bad Request` — `{ "detail": "Adjustment would result in negative balance" }`

### TC-API-HOUR-11: GET /customer-hours/remaining/:customer_id — 404 when not found
- **Input:** unknown customer_id
- **Expected:** `404 Not Found`

### TC-API-HOUR-12: POST /customer-hours/deduct — concurrent deduction race condition
- **Steps:**
  1. Customer with balance=1
  2. Simultaneously send 2 POST /customer-hours/deduct
- **Expected:** One succeeds `200 OK`; one fails `400 Bad Request`; final balance=0 (never -1)

---

## TC-API-TRAINER Additional

### TC-API-TRAINER-04: GET /trainers — owner sees all branches
- **Auth:** owner_token
- **Expected:** Trainers from all branches within partner returned

### TC-API-TRAINER-05: PUT /trainers/:id — update trainer info
- **Auth:** admin_token
- **Input:** Updated email and status
- **Expected:** `200 OK` — updated trainer returned

### TC-API-TRAINER-06: DELETE /trainers/:id — fail if trainer has active booking
- **Auth:** admin_token
- **Precondition:** Trainer has upcoming confirmed booking
- **Expected:** `409 Conflict` — `{ "detail": "Trainer has active bookings" }`

---

## TC-API-PKG Additional

### TC-API-PKG-05: DELETE /packages — success when no active orders
- **Auth:** owner_token
- **Expected:** `204 No Content`

### TC-API-PKG-06: DELETE /packages — fail if package used in active orders
- **Auth:** owner_token
- **Precondition:** Package referenced in existing order
- **Expected:** `409 Conflict` — `{ "detail": "Package is referenced by existing orders" }`

### TC-API-PKG-07: GET /packages — package before active period excluded when active_only=true
- **Params:** `?active_only=true`
- **Precondition:** Package with `active_from` = tomorrow
- **Expected:** Package not included in response

---

## TC-API-USER Additional

### TC-API-USER-06: DELETE /users/:id — deactivate user
- **Auth:** owner_token
- **Expected:** `200 OK` — user status = inactive

### TC-API-USER-07: DELETE /users/:id — cannot deactivate own account
- **Auth:** owner_token
- **Input:** own user_id
- **Expected:** `400 Bad Request` — `{ "detail": "Cannot deactivate your own account" }`

### TC-API-USER-08: DELETE /users/:id — cannot deactivate user with higher role
- **Auth:** branch_master_token
- **Input:** owner user_id
- **Expected:** `403 Forbidden`

---

## TC-API-DASH Additional

### TC-API-DASH-06: GET /dashboard — branch_master sees branch summary
- **Auth:** branch_master_token (Pattaya)
- **Expected:** `200 OK` — `{ total_orders, total_revenue, breakdown_by_admin: [...], breakdown_by_trainer: [...] }` scoped to Pattaya

### TC-API-DASH-07: GET /dashboard — branch_master breakdown per admin
- **Auth:** branch_master_token
- **Expected:** Each admin in branch listed with order_count and revenue

### TC-API-DASH-08: GET /dashboard — branch_master breakdown per trainer
- **Auth:** branch_master_token
- **Expected:** Each trainer in branch listed with session_count and hours_trained

---

## TC-API-BOOK Additional

### TC-API-BOOK-08: POST /bookings/external — external customer request
- **Auth:** external service API key
- **Input:** `{ "customer_id": "...", "branch_id": "...", "start_time": "...", "slots": 2 }`
- **Expected:** `201 Created` — status = "pending"

### TC-API-BOOK-09: POST /bookings/external — non-contiguous slots rejected
- **Input:** slots not consecutive within same day
- **Expected:** `400 Bad Request` — `{ "detail": "Slots must be contiguous within the same day" }`

### TC-API-BOOK-10: POST /bookings/external — cross-day slots rejected
- **Input:** slots spanning midnight
- **Expected:** `400 Bad Request` — `{ "detail": "Booking must be within the same day" }`

### TC-API-BOOK-11: PUT /bookings/:id/confirm — admin can confirm
- **Auth:** admin_token
- **Expected:** `200 OK` — status = "CONFIRMED"

### TC-API-BOOK-11b: PUT /bookings/:id/confirm — trainer cannot confirm
- **Auth:** trainer_token
- **Expected:** `403 Forbidden`

### TC-API-BOOK-12: DELETE /bookings/:id — cancel returns session (policy = return)
- **Precondition:** cancel_policy.return_hour = true
- **Steps:**
  1. Customer balance = N
  2. DELETE /bookings/:id
  3. GET /customer-hours/remaining/:customer_id
- **Expected:** balance = N+1; session log entry type=HOUR_ADJUST created

### TC-API-BOOK-13: DELETE /bookings/:id — cancel does not return session (policy = no return)
- **Precondition:** cancel_policy.return_hour = false
- **Steps:**
  1. Customer balance = N
  2. DELETE /bookings/:id
  3. GET /customer-hours/remaining/:customer_id
- **Expected:** balance = N (unchanged)

### TC-API-BOOK-14: GET /bookings?start_date=&end_date= — filter by date range
- **Auth:** admin_token
- **Expected:** Only bookings within range returned

### TC-API-BOOK-15: GET /bookings?trainer_id= — filter by trainer
- **Auth:** admin_token
- **Expected:** Only bookings for that trainer returned

---

## TC-API-CANCEL-POLICY — Cancel Policy Settings

### TC-API-CANCEL-01: GET /settings/cancel-policy — returns current policy
- **Auth:** owner_token
- **Expected:** `200 OK` — `{ "hours_before": 24, "return_hour": true }`

### TC-API-CANCEL-02: PUT /settings/cancel-policy — owner can update
- **Auth:** owner_token
- **Input:** `{ "hours_before": 12, "return_hour": false }`
- **Expected:** `200 OK` — updated policy returned

### TC-API-CANCEL-03: PUT /settings/cancel-policy — admin cannot update
- **Auth:** admin_token
- **Expected:** `403 Forbidden`

---

## TC-API-CARE — Caretaker API

### TC-API-CARE-01: GET /caretakers — returns list filtered by branch
- **Auth:** admin_token (Pattaya)
- **Expected:** `200 OK` — only Pattaya caretakers returned

### TC-API-CARE-02: GET /caretakers — owner sees all branches
- **Auth:** owner_token
- **Expected:** Caretakers from all branches returned

### TC-API-CARE-03: POST /caretakers — create valid caretaker
- **Auth:** admin_token
- **Input:** `{ "name": "...", "email": "...", "branch_id": "...", "status": "ACTIVE" }`
- **Expected:** `201 Created`

### TC-API-CARE-04: POST /caretakers — admin cannot create for other branch
- **Auth:** admin_token (Pattaya)
- **Input:** `{ "branch_id": "kanchanaburi_id" }`
- **Expected:** `403 Forbidden`

### TC-API-CARE-05: PUT /caretakers/:id — update caretaker
- **Auth:** admin_token
- **Input:** Updated name and status
- **Expected:** `200 OK`

### TC-API-CARE-06: DELETE /caretakers/:id — success
- **Auth:** admin_token
- **Expected:** `204 No Content`

---

## TC-API-PRINT — Signature Print API

### TC-API-PRINT-01: POST /signature-print/generate — generate Google Sheet
- **Auth:** admin_token (Google Drive connected)
- **Input:** `{ "order_id": "..." }`
- **Expected:** `200 OK` — `{ "file_url": "https://docs.google.com/...", "file_id": "..." }`

### TC-API-PRINT-02: POST /signature-print/generate — blocked when not connected
- **Auth:** admin_token (no Google Drive connected)
- **Expected:** `400 Bad Request` — `{ "detail": "Google Drive not connected" }`

### TC-API-PRINT-03: GET /signature-print/list — returns generated files
- **Auth:** admin_token
- **Expected:** `200 OK` — list with: order_id, file_url, created_at

### TC-API-PRINT-04: GET /signature-print/storage — returns Drive storage info
- **Auth:** admin_token
- **Expected:** `200 OK` — `{ "used_bytes": N, "total_bytes": N, "used_gb": "5.0", "total_gb": "15.0" }`

---

## TC-API-GOOGLE — Google Account Settings API

### TC-API-GOOGLE-01: POST /settings/google/connect — connect Google Account
- **Auth:** admin_token
- **Input:** OAuth code from Google
- **Expected:** `200 OK` — `{ "connected_email": "...", "connected": true }`

### TC-API-GOOGLE-02: DELETE /settings/google/disconnect — disconnect
- **Auth:** admin_token
- **Expected:** `200 OK` — Google token removed from DB

### TC-API-GOOGLE-03: GET /settings/google/storage — returns storage usage
- **Auth:** admin_token (connected)
- **Expected:** `200 OK` — storage data from Drive API

### TC-API-GOOGLE-04: GET /settings/google/storage — error when not connected
- **Auth:** admin_token (not connected)
- **Expected:** `400 Bad Request` — `{ "detail": "Google Drive not connected" }`

---

## TC-API-HELP — Help Page API

### TC-API-HELP-01: GET /help/manual — returns role-specific content
- **Auth:** master_token
- **Expected:** `200 OK` — only sections relevant to trainer role returned

### TC-API-HELP-02: GET /help/manual — owner sees full manual
- **Auth:** owner_token
- **Expected:** All sections returned

### TC-API-HELP-03: GET /help/line-qr — returns developer + branch QR
- **Auth:** admin_token (Pattaya)
- **Expected:** `200 OK` — `{ "developer_qr_url": "...", "branch_qr_url": "..." }` — branch QR matches Pattaya

---

## TC-API-BRANCH Additional

### TC-API-BRANCH-04: POST /branches — owner creates new branch
- **Auth:** owner_token
- **Input:** `{ "name": "Bangkok", "prefix": "BKK", "source_types": [...], "opening_time": "09:00", "closing_time": "21:00" }`
- **Expected:** `201 Created`

### TC-API-BRANCH-05: POST /branches — admin cannot create branch
- **Auth:** admin_token
- **Expected:** `403 Forbidden`

### TC-API-BRANCH-06: PUT /branches/:id — update source type → customer code uses new code
- **Auth:** owner_token
- **Steps:**
  1. Update source type code from "PAT" to "PTY"
  2. POST /customers with that source
- **Expected:** New customer code uses "PTY" not "PAT"

---

## TC-API-LOG Additional

### TC-API-LOG-05: Activity log created on order.create
- **Steps:** POST /orders → GET /activity-log
- **Expected:** Entry with action="order.create"

### TC-API-LOG-06: Activity log created on order.edit
- **Steps:** PUT /orders/:id → GET /activity-log
- **Expected:** Entry with action="order.edit"; changes field shows what changed

### TC-API-LOG-07: Activity log created on booking.confirm
- **Steps:** PUT /bookings/:id/confirm → GET /activity-log
- **Expected:** Entry with action="booking.confirm"

### TC-API-LOG-08: Activity log created on booking.cancel
- **Steps:** DELETE /bookings/:id → GET /activity-log
- **Expected:** Entry with action="booking.cancel"

### TC-API-LOG-09: Activity log created on user.create
- **Steps:** POST /users → GET /activity-log
- **Expected:** Entry with action="user.create"

### TC-API-LOG-10: Activity log created on permission.update
- **Steps:** PUT /permissions → GET /activity-log
- **Expected:** Entry with action="permission.update"

### TC-API-LOG-11: Activity log created on customer.edit
- **Steps:** PUT /customers/:id → GET /activity-log
- **Expected:** Entry with action="customer.edit"

### TC-API-LOG-12: Activity log created on customer.delete
- **Steps:** DELETE /customers/:id → GET /activity-log
- **Expected:** Entry with action="customer.delete"

### TC-API-LOG-13: Activity log created on customer_hour.adjust
- **Steps:** PUT /customer-hours/adjust → GET /activity-log
- **Expected:** Entry with action="customer_hour.adjust"

---

## TC-API-SEC — Security

### TC-API-SEC-01: SQL Injection — query param sanitized
- **Input:** `GET /customers?search='; DROP TABLE customers; --`
- **Expected:** `200 OK` or `400` — no DB error; no data corruption

### TC-API-SEC-02: SQL Injection — body field sanitized
- **Input:** POST /customers with `{ "first_name": "'; DROP TABLE customers; --" }`
- **Expected:** `422` or saved as plain text — no DB error

### TC-API-SEC-03: Token cross-partner isolation
- **Auth:** owner_token from Partner A
- **Input:** GET /customers?branch_id= (Partner B's branch)
- **Expected:** `403 Forbidden` — no data leakage across partners

---

## TC-API-INTEGRITY — Data Integrity

### TC-API-INT-01: DELETE /branches/:id — fail if branch has customers
- **Auth:** owner_token
- **Precondition:** Branch has existing customers
- **Expected:** `409 Conflict` — `{ "detail": "Branch has existing customers" }`

### TC-API-INT-02: DELETE /trainers/:id — fail if trainer has active booking
- **Auth:** admin_token
- **Precondition:** Trainer has upcoming confirmed booking
- **Expected:** `409 Conflict` — `{ "detail": "Trainer has active bookings" }`

### TC-API-INT-03: DELETE /packages/:id — fail if package used in order
- **Auth:** owner_token
- **Precondition:** Package referenced in existing order
- **Expected:** `409 Conflict`

### TC-API-INT-04: Session balance never negative — DB constraint
- **Steps:**
  1. Customer balance=1
  2. 2 concurrent POST /customer-hours/deduct
  3. Query DB directly for hour_balance
- **Expected:** balance = 0 (never -1); DB constraint enforced

### TC-API-INT-05: Customer code unique at DB level
- **Steps:**
  1. 2 concurrent POST /customers (same branch, same source)
  2. Query DB for customer codes
- **Expected:** Both codes unique; no duplicates in DB

---

## TC-API-VALIDATE — Input Validation

### TC-API-VAL-01: Future birthdate rejected
- **Input:** POST /customers with `{ "birthdate": "2099-01-01" }`
- **Expected:** `422 Unprocessable Entity` — birthdate cannot be in the future

### TC-API-VAL-02: Invalid email format rejected across endpoints
- **Input:** POST /customers, POST /trainers, POST /caretakers with `{ "email": "bad-email" }`
- **Expected:** `422 Unprocessable Entity`

### TC-API-VAL-03: Negative hours rejected in order
- **Input:** POST /orders with `{ "hours": -1, "bonus_hours": -2 }`
- **Expected:** `422 Unprocessable Entity`

### TC-API-VAL-04: Negative price rejected
- **Input:** POST /orders with `{ "total_price": -500 }`
- **Expected:** `422 Unprocessable Entity`


---

## TC-API-AUTH Additional v2 — New Auth Flow

### TC-API-AUTH-16: POST /auth/login — returns temporary token (not JWT)
- **Input:** `{ "email": "owner@test.com", "password": "valid_pass" }`
- **Expected:** `200 OK` — `{ "temporary_token": "...", "token_type": "temporary" }`
- **Assert:** Response does NOT contain `access_token` — JWT only issued after PIN

### TC-API-AUTH-17: POST /auth/pin/verify — returns JWT access token
- **Precondition:** temporary_token obtained from /auth/login
- **Input:** `{ "pin": "123456" }` with temporary_token in Authorization header
- **Expected:** `200 OK` — `{ "access_token": "...", "token_type": "bearer" }`
- **Assert:** JWT is valid and can be used for protected endpoints

### TC-API-AUTH-18: Protected route with temporary token (pre-PIN) returns 401
- **Input:** `GET /customers` with temporary_token (before PIN verified)
- **Expected:** `401 Unauthorized` — token is not a full JWT yet

### TC-API-AUTH-19: POST /auth/password/forgot — sends reset email
- **Input:** `{ "email": "owner@test.com" }`
- **Expected:** `200 OK` — reset email sent (check mock inbox)

### TC-API-AUTH-20: POST /auth/password/forgot — unknown email returns 200 (security)
- **Input:** `{ "email": "nobody@test.com" }`
- **Expected:** `200 OK` — same response regardless (prevent email enumeration)

### TC-API-AUTH-21: POST /auth/password/reset — valid token resets password
- **Input:** `{ "token": "valid_reset_token", "new_password": "NewPass123" }`
- **Expected:** `200 OK` — password updated; can login with new password

### TC-API-AUTH-22: POST /auth/password/reset — expired token returns 400
- **Input:** `{ "token": "expired_token", "new_password": "NewPass123" }`
- **Expected:** `400 Bad Request` — `{ "detail": "Reset token expired or invalid" }`

### TC-API-AUTH-23: POST /auth/password/change — change password while logged in
- **Auth:** JWT + PIN
- **Input:** `{ "old_password": "current_pass", "new_password": "NewPass123" }`
- **Expected:** `200 OK` — password updated

### TC-API-AUTH-24: POST /auth/password/change — wrong old password returns 401
- **Auth:** JWT + PIN
- **Input:** `{ "old_password": "wrong", "new_password": "NewPass123" }`
- **Expected:** `401 Unauthorized`

### TC-API-AUTH-25: POST /internal/assign-password — developer API key assigns password
- **Auth:** Developer API Key (X-API-Key header)
- **Input:** `{ "new_password": "ForcedPass123" }`
- **Expected:** `200 OK` — user can login with new password

### TC-API-AUTH-26: POST /internal/assign-pin — developer API key assigns PIN + unlocks
- **Auth:** Developer API Key
- **Input:** `{ "new_pin": "999999" }`
- **Expected:** `200 OK` — PIN updated; pin_locked = false; pin_attempts = 0 in DB

### TC-API-AUTH-27: POST /internal/* — regular JWT cannot access internal endpoints
- **Auth:** admin_token (regular JWT)
- **Expected:** `403 Forbidden` — internal endpoints require Developer API Key only

