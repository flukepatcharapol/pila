# Studio Management — System Requirements
## Version 1.0 | 2026-04-07
### Sources: app-context.md + FE Design (Azure Studio Pro) + FE Requirements Analysis + Test Cases V0.2

---

## 1. Project Overview

| Item | Detail |
|------|--------|
| **System Name** | Studio Management (Pila Studio) |
| **Rebuilt From** | Boston Pilates (Google AppSheet + Google Sheets) |
| **Target Platform** | Web Application — Desktop/Tablet first |
| **Primary Users** | Studio Owner, Branch Manager, Admin Staff, Trainers |
| **Current Branches** | Pattaya, Chachoengsao, Kanchanaburi |

---

## 2. Design System

### 2.1 Brand Identity: "The Mindful Curator"
The UI philosophy treats the screen as a gallery space — premium, serene, editorial. Inspired by the precision and flow of Pilates.

### 2.2 Color Tokens
| Token | Hex | Usage |
|-------|-----|-------|
| Primary (Deep Sea) | `#162839` | Navigation, headers, primary buttons |
| Secondary (Steel Blue) | `#395f94` | Interactive elements, branch_master badge |
| Accent (Muted Teal) | `#54b6b5` | CTAs, success states, admin badge |
| Surface | `#f8fafb` | Base canvas |
| Surface Container Low | `#f2f4f5` | Secondary content areas |
| Surface Container Lowest | `#ffffff` | Cards, elevated components |
| On Surface | `#191c1d` | All text (never pure black) |
| On Surface Variant | `#43474c` | Secondary text |

### 2.3 Typography
| Scale | Font | Size | Usage |
|-------|------|------|-------|
| Display | Manrope | 3.5rem | Hero headers |
| Headline | Manrope | 1.75rem | Page titles |
| Title | Manrope | 1.375rem | Section headers |
| Body | Inter | 0.875rem | General content |

- Thai text line-height: **1.6× font size** (prevents tone mark clipping)
- Letter-spacing headlines: `-0.02em`

### 2.4 Key Design Rules
- **No 1px divider lines** — use background tonal shifts only
- **Glassmorphism** on floating elements: `backdrop-blur(12px)`, surface at 80% opacity
- **Ambient shadows only**: `0px 20px 40px rgba(25,28,29,0.06)`
- **Corner radius**: `xl` = 0.75rem cards, `lg` = 0.5rem buttons, `full` = pills
- **Whitespace**: Always add 20% more than you think is needed
- **Ghost Border**: If boundary required, use `outline-variant` at 15% opacity only

### 2.5 Screens Designed (FE Design ZIP)
| Screen | File |
|--------|------|
| Login | `login_screen/` |
| Admin Dashboard | `streamlined_admin_dashboard/` |
| Customer Management List | `updated_customer_management/` |
| Add/Edit Customer Form | `updated_add_new_customer_form_navigation/` |
| Simplified Order Management | `simplified_order_management/` |
| Session Deduction | `updated_session_deduction_management/` |
| Customer Session Hours View | `customer_session_management_hours_view/` |
| Customer Session Table View | `customer_session_focused_table_view/` |
| Trainer Directory | `trainer_directory_table_view/` |
| Vertical Trainer Schedule | `vertical_trainer_schedule_view/` |
| Package List | `package_management_list_view/` |
| Add/Edit Package Form | `add_edit_package_form/` |
| User Management + Slide-out | `user_management_slide_out_details/` |
| Branch Configuration | `updated_branch_configuration/` |
| Settings Layout | `updated_settings_layout/` |
| Caretaker/Consultant Directory | `consultant_directory/` |

---

## 3. User Roles & Hierarchy

```
developer (top — cross-partner)
  └── owner (cross-branch within partner)
        └── branch_master (within assigned branch, full access)
              └── admin (within branch, permission-matrix gated)
                    └── trainer (within branch, permission-matrix gated)
```

| Role | Scope | Can Create Users |
|------|-------|-----------------|
| `developer` | All partners, all branches | Any role |
| `owner` | Own partner, all branches | branch_master, admin, trainer |
| `branch_master` | Assigned branch only | admin, trainer (own branch only) |
| `admin` | Assigned branch only | None |
| `trainer` | Assigned branch only | None |

### Role Badge Colors (UI)
| Role | Color |
|------|-------|
| developer | Purple |
| owner | Deep Sea `#162839` |
| branch_master | Steel Blue `#395f94` |
| admin | Muted Teal `#54b6b5` |
| trainer | Grey |

---

## 4. Authentication System

### 4.1 Login Flow
```
Step 1: Email + Password → POST /auth/login → ได้ temporary token (ไม่ใช่ JWT)
Step 2: PIN entry (6-digit) → POST /auth/pin/verify → ได้ JWT จริง (เริ่มใช้งานได้)
Step 3: Access granted → Dashboard
```

> ⚠️ JWT จะออกให้หลัง PIN verify เท่านั้น ไม่ใช่หลัง email+password login

### 4.2 Session Rules
- **PIN session**: expires every **5 hours** → re-enter PIN only (no full re-login)
- **Login session**: duration configurable by developer
- **Forgot PIN**: OTP sent to email → `/pin/reset`
- **PIN lockout**: locked after 5 wrong attempts → must reset via OTP
- **OTP rate limit**: max 3 requests per 60 seconds → `429 Too Many Requests`
- **Login brute force**: blocked after 10 wrong password attempts → `429`

### 4.3 Password Policy
- Stored as **bcrypt hash** in DB — not reversible
- ลืม password → Branch Manager หรือ Owner reset ให้ได้ผ่าน User Management UI
- Developer reset ได้ผ่าน `/internal/assign-password/:user_id` (API Key เท่านั้น, ไม่มี UI)
- No self-service password reset — accounts created by Branch Manager or Owner only
- No self-registration

---

## 5. Customer Code System

### Format
```
[BranchPrefix]-[SourceCode][RunningNumber]
```

### Examples
| Branch | Source | Code |
|--------|--------|------|
| Pattaya | Page (MKT) | `BPY-MKT001` |
| Pattaya | Walk In (PAT) | `BPY-PAT001` |
| Chachoengsao | Page (MKT) | `BCC-MKT001` |
| Kanchanaburi | Page (MKT) | `BKB-MKT001` |

### Rules
- Running number increments **per Branch × Source Type** independently
- BranchPrefix and SourceCode are configurable via Branch Config
- Code is auto-generated, read-only after creation
- Unique constraint enforced at DB level
- Concurrent creation must not produce duplicates (use DB lock / atomic counter)

---

## 6. Modules & Functional Requirements

---

### 6.1 Customer Management

**Routes:** `/customers`, `/customers/new`, `/customers/:id`, `/customers/:id/edit`

**Fields:**
- Branch (required), Source Type (required) → generates Customer Code
- Trainer assignment (chip, filtered by branch) → used for autofill in orders
- Caretaker assignment (chip, filtered by branch) → used for autofill in orders
- First name, Last name, Nickname, Display name
- Contact channel (Phone/LINE), Phone number, LINE ID, Email
- Status (Active/Inactive), Notes
- Profile photo, Birthday, Is Duplicate flag

**Business Rules:**
- Customer Code auto-generated on branch + source selection
- Trainer/Caretaker chip must filter by selected branch
- Display name auto-suggested from nickname
- Admin/Master sees only own branch customers
- Owner sees all branches within partner
- Customer detail shows: order history, remaining session hours

---

### 6.2 Order Management

**Routes:** `/orders`, `/orders/new`, `/orders/:id`, `/orders/:id/edit`

**Fields:**
- Order date, Customer (search dropdown), Trainer (auto-filled), Caretaker (auto-filled)
- Package (chip, active + branch-matched), Hours (stepper), Bonus hours (stepper)
- Payment method (Credit/Bank Transfer), Total price, Price per session
- Installment plan, Outstanding balance, Renew flag, Notes, Branch

**Business Rules:**
- Trainer/Caretaker auto-filled from customer profile (editable)
- Package selector: active status + branch scope match only
- Package before active period → blocked
- Receipt/Invoice email sent automatically on save
- Outstanding balance badge shown on order list rows
- Negative hours/price → `422 Unprocessable Entity`

**Payment Tracking (sub-module):**
- Record installment payments: `POST /orders/:id/payments`
- View installment history: `GET /orders/:id/payments`
- Resend receipt: `POST /orders/:id/receipt`

---

### 6.3 Session System

#### Session Deduction
**Route:** `/sessions/deduct`
- Select Branch → select Customer (by name/code, never UUID) → Deduct
- Shows deduction history table after customer selected
- Filter by date range
- Zero balance → blocked with error

#### Session Log
**Route:** `/sessions/log`
- All transaction types: Purchased, Session Claim, Edit Session, New Customer, Adjust
- Columns: Timestamp, Customer Code, Name, Transaction Type, Before, Amount, After, Actor
- Filter: date range, customer, branch

#### Trainer Training Report
**Route:** `/sessions/trainer-report`
- Quick filter: Today / This Month
- Date range + Branch + Trainer selector
- Summary cards: total hours, session count
- History table: Date/Time, Trainer, Customer, Hours

#### Session Balance
**Route:** `/sessions/remaining/:customer_id`
- Current remaining hours per customer
- Auto-updated on order creation, deduction, or adjustment

#### Manual Session Adjust
**Endpoint:** `PUT /sessions/adjust`
- Positive or negative adjustment with reason
- Cannot adjust below zero
- Creates ADJUST transaction log entry
- Creates activity log entry

---

### 6.4 Trainer Management

**Routes:** `/trainers`, `/trainers/new`, `/trainers/:id/edit`

**Fields:** Name, Display name (auto: Name:Branch), Status, Email, Profile photo, Branch

**Business Rules:**
- Admin sees only own branch trainers
- Owner sees all branches
- Cannot delete trainer with active customers → `409 Conflict`
- Cannot delete trainer with active booking → `409 Conflict`

---

### 6.5 Package Management

**Routes:** `/packages`, `/packages/new`, `/packages/:id/edit`

**Fields:** Name, Hours, Type (Sale/Pre-sale), Price, Branch scope (All / Selected), Active period (optional), Status

**Business Rules:**
- Branch scope: All → available everywhere; Selected → specific branches only
- Active period optional: if set, package only available within that date range
- Pre-active package excluded from order form
- Expired package shows "Expired" badge; excluded from order form
- Cannot delete package referenced in existing orders → `409 Conflict`

**Status Badges:** Active (teal) / Inactive (grey) / Expired (red)

---

### 6.6 Booking + Staff Schedule

**Route:** `/booking`

**Timetable View:**
- Default: 3-day view (today + 2 days ahead)
- Toggle: Full week (7 days)
- Navigate: prev/next buttons
- Slots: 30-minute intervals
- Time range: per branch opening/closing hours
- Unlimited bookings per slot (stacked display)

**Color Coding:**
- Staff schedule: Blue
- Customer booking: Teal
- Pending: Amber

**Role-based Actions:**
| Role | Can Do |
|------|--------|
| Trainer | Schedule own slots only, multi-select |
| Admin | Schedule trainers + Book customers, multi-select, see all trainer schedules |
| Customer (API) | Request booking — contiguous slots, same day only |

**Booking Status Flow:**
```
Pending → Confirmed (Admin/Owner only) → Cancelled (Admin/Owner only)
```

**Confirm Flow:**
- Admin confirms → if customer has LINE → show "Notify customer?" prompt
- If no LINE → no prompt shown

**Cancel Policy (configurable):**
- `hours_before`: minimum hours before booking to allow cancel
- `return_session`: whether to return session balance on cancel

**External API (from customer product):**
- `GET /bookings` — available slots + trainers
- `POST /bookings/external` — create pending booking
- Slots must be contiguous within same day
- Customer can only book own branch

---

### 6.7 Dashboard

**Route:** `/dashboard`

| Role | Cards |
|------|-------|
| trainer | Hours trained today/MTD, customer count, bookings |
| admin | Orders today, sessions deducted today |
| branch_master | Total orders, revenue, breakdown by admin + trainer |
| owner | branch_master view + all branches + branch selector |
| developer | Owner view + partner selector + cross-partner aggregate |

**Components:** Summary stat cards, line/bar chart, time range filter (Today/Week/Month/Custom), branch selector (owner+), partner selector (developer only)

**States:** Loading skeleton / Populated / Empty / Error

---

### 6.8 Permission Management

**Route:** `/permissions`

**Matrix:** Module rows × Role columns (action-level: View/Create/Edit/Delete)

**Columns visible per role:**
| Role | Columns |
|------|---------|
| developer | owner, branch_master, admin, trainer |
| owner | branch_master, admin, trainer |
| branch_master | admin, trainer |
| admin | No access (403) |
| trainer | No access (403) |

**Feature Toggle:** Module-level on/off switch above matrix
- FE: shows overlay "ฟีเจอร์นี้ไม่พร้อมใช้งาน" when disabled
- BE: guards all API endpoints of that module
- Takes effect immediately without re-login

---

### 6.9 User Management

**Route:** `/users`

**Components:** Role/Branch/Status filter, grouped Active/Inactive table, slide-out detail panel, Add User button (role-gated)

**Fields:** Username, Password (masked, bcrypt stored), Role, Branch

**Business Rules:**
- Cannot create user with equal or higher role than self
- Branch Manager creates only for own branch
- Cannot deactivate own account
- Cannot deactivate user with higher role
- Role badge colors per design system

---

### 6.10 Activity Log

**Route:** `/activity-log`

**Columns:** Timestamp, Actor, Action Type, Target, Changes (before/after), Branch

**Filters:** Date range, User/Actor, Action type, Branch

**Logged Actions:**
customer.create, customer.edit, customer.delete, order.create, order.edit,
session.deduct, session.adjust, booking.confirm, booking.cancel,
user.create, permission.update

**Role Scoping:** Admin sees own branch only; Owner sees all branches

---

### 6.11 Branch Config

**Route:** `/settings/branches`

**Fields per branch:** Name, Prefix (e.g. BPY), Source Types (list of label+code), Opening time, Closing time

**Business Rules:**
- Owner only can create/edit branches
- Changing source type code affects new customer codes only (existing unaffected)
- Opening/closing hours feed into Booking timetable time range
- Cannot delete branch with existing customers → `409 Conflict`

---

### 6.12 Caretaker Management

**Route:** `/caretakers`

**Fields:** Name, Email, Branch, Status (Active/Inactive)

**Business Rules:**
- List grouped by branch
- Admin sees own branch only
- Caretaker appears in Customer form and Order form (filtered by branch)
- Admin cannot create caretaker for other branch → `403`

---

### 6.13 Signature Print

**Route:** `/signature-print`

**Features:**
- Connect Google Account (OAuth)
- Generate Google Sheet from order → save to Google Drive
- Format/margin/layout must match original template exactly
- Returns shareable link
- List of previously generated files
- Google Drive storage widget (X GB / Y GB) — via Drive API `about.get`
- Storage warning when >90% full
- Blocked if Google Drive not connected

---

### 6.14 Settings

**Route:** `/settings`

**Components:**
- Language toggle (Thai / English) — persists across sessions
- Dark mode toggle — persists across sessions
- Google Account connection + status
- Google Drive storage gauge
- Profile section (Name, Role, Branch — read-only)

---

### 6.15 Help Page

**Route:** `/help`

**Components:**
- User manual (auto-generated, role-specific — shows only accessible features)
- Search within manual
- LINE QR codes: Developer contact + per-branch group chat (matches user's branch)
- Expandable FAQ sections

---

## 7. Cross-Cutting Requirements

| # | Requirement |
|---|-------------|
| CR-01 | All dropdowns showing people/customers must display Name+Code, never UUID |
| CR-02 | Chip selectors for Trainer/Caretaker must filter by selected Branch |
| CR-03 | Sidebar shows only menu items the current role has permission to access |
| CR-04 | Feature Toggle: overlay "ฟีเจอร์นี้ไม่พร้อมใช้งาน" when module disabled |
| CR-05 | All forms must have loading state, success toast, and error toast |
| CR-06 | Tables must support pagination (max 100/page), sorting, keyword search |
| CR-07 | Thai language support — line-height 1.6× for Thai characters |
| CR-08 | Responsive: functional on tablet (≥768px), optimized for desktop (≥1280px) |
| CR-09 | Active branch always visible in sidebar header |
| CR-10 | All destructive actions require confirmation dialog |
| CR-11 | No raw UUIDs visible anywhere in UI |
| CR-12 | All algorithm code must have inline comments (see coding standards) |
| CR-13 | Business rules must be explained in plain language in code comments |
| CR-14 | Every line of algorithm logic must be commented as a tutorial for junior devs |
| CR-15 | Naming consistency: column/field names must be consistent across all tables, models, schemas, and API responses — e.g. if a field is called `user_id` in one table, all other tables referring to the same concept must also use `user_id`, not `actor_id`, `created_by_id`, or any other variation. When in doubt, align with the most common usage across the codebase |

---

## 8. Security Requirements

| # | Requirement |
|---|-------------|
| SEC-01 | Passwords stored as bcrypt hash — never plaintext |
| SEC-02 | JWT tokens expire per config; PIN tokens expire in 5 hours |
| SEC-03 | BE guards every API endpoint independently (not just FE hiding) |
| SEC-04 | No sensitive data (token, password, PIN) stored in browser localStorage |
| SEC-05 | SQL injection protection on all query params and body fields |
| SEC-06 | Token cannot be used across partners (cross-partner isolation) |
| SEC-07 | XSS: all user input sanitized before rendering |
| SEC-08 | Rate limiting: login (10 attempts), OTP (3/60s), PIN lockout (5 attempts) |

---

## 9. Data Integrity Requirements

| # | Requirement |
|---|-------------|
| INT-01 | Session balance cannot go negative (DB constraint + app logic) |
| INT-02 | Customer code unique at DB level (unique constraint) |
| INT-03 | Cannot delete Branch with existing customers → 409 |
| INT-04 | Cannot delete Trainer with active customers or bookings → 409 |
| INT-05 | Cannot delete Package referenced in orders → 409 |
| INT-06 | Concurrent session deduction must use DB row lock (SELECT FOR UPDATE) |
| INT-07 | Concurrent customer code generation must be atomic |
| INT-08 | All write operations must create corresponding activity log entries |

---

## 10. API Design Principles

| # | Principle |
|---|-----------|
| API-01 | RESTful endpoints with standard HTTP status codes |
| API-02 | All responses must use human-readable display values (no UUIDs in response display fields) |
| API-03 | Role-based scoping applied at API level (not just FE) |
| API-04 | Pagination: default 20/page, max 100/page |
| API-05 | All list endpoints support: filter, search, sort, pagination |
| API-06 | External booking API uses separate API key authentication |
| API-07 | Feature toggle check on every protected endpoint |
| API-08 | Permission matrix check on every module endpoint |

---

## 11. Coding Standards

> Full details in `00_coding_standards.md`

| Rule | Description |
|------|-------------|
| Every algorithm line | Has inline `#` comment explaining what AND why |
| Business rules | Explained in plain Thai or English in comments |
| Guard clauses | Explain what condition is blocked and why |
| DB operations | Explain what is queried/saved and the effect |
| Test assertions | Explain what bug this test is preventing |
| Magic numbers | Always named with constant or comment |

---

## 12. Future Plans (Out of Scope for V1)

| Feature | Notes |
|---------|-------|
| Tax & Accounting | Feature toggle; needs accountant consultation first |
| Loyalty Coin System | Multi-currency per partner; feature toggle |
| Multi-Tenant Platform | New platform; migrate Boston Pilates into it |
| Performance benchmarks | Define thresholds after MVP |
| Accessibility (a11y) | WCAG AA compliance — future sprint |

---

## 13. Test Coverage Summary

| Test Suite | File | TCs |
|-----------|------|-----|
| FE (Playwright/Python) | `02_fe_testcases_V_0_2.md` | ~120 |
| BE (pytest/httpx) | `03_be_testcases_V_0_2.md` | ~165 |
| Integration (E2E) | `04_integration_testcases_V_0_2.md` | ~70 |

---

## 14. Pipeline Status

| Step | Description | Status | Output Files |
|------|-------------|--------|--------------|
| 1 | App Context + UI Screenshots | ✅ Done | `app-context.md`, `studio-management.zip` |
| 2 | New System Requirements | ✅ Done | `app-context.md`, `requirements.md` |
| 3 | FE Design (Stitch AI) | ✅ Done | `FE_Design.zip` — 18 screens |
| 4 | FE Requirements Analysis | ✅ Done | `01_fe_requirements_analysis.md` |
| 5 | Coding Standards | ✅ Done | `00_coding_standards.md` |
| 6 | System Requirements Doc | ✅ Done | `requirements.md` |
| 7 | Test Cases — FE | ✅ Done | `02_fe_testcases_V_0_2.md` (~120+ TCs) |
| 8 | Test Cases — BE | ✅ Done | `03_be_testcases_V_0_2.md` (~170+ TCs) |
| 9 | Test Cases — Integration | ✅ Done | `04_integration_testcases_V_0_2.md` (~70 TCs) |
| 10 | BE Design — DB Schema + API Spec | ✅ Done | `05_be_design.md` (v1.2) |
| 11 | Automation Test Plan + Scripts | ✅ Done | `06_automation_test_plan.md`, `common_api.py`, `common_web.py` |
| 12 | Setup & README | ✅ Done | `SETUP.md`, `BE_README.md`, `FE_README.md` |
| 13 | Build BE (FastAPI + PostgreSQL) | ✅ Done | API code, DB migrations, 204 BE tests passing |
| 14 | BE Tests Pass (pytest + Allure) | ✅ Done | All 204 BE tests passing w/ --keep-db isolation |
| 15 | Build FE UI + Connect API (E2E) | ✅ Done | React app, API integration, auth dual-session |
| 16 | FE + E2E Tests Pass (Playwright) | ⏳ In Progress | All FE + integration test cases green |
| 17 | CI/CD Pipeline + Deploy (dev/prod) | ⬜ Pending | GitHub Actions, domain, env separation |
| 18 | Scheduled Test Runs | ⬜ Pending | Cron-based test automation |

### Current Status
> **Now at Step 16** — FE + E2E Tests Pass (Playwright) | Previous: Steps 13-15 complete (auth dual-session fully implemented)

---

### Step Details

**Step 13 — Build BE**
- FastAPI application + SQLAlchemy models
- Alembic DB migrations
- All API endpoints per `05_be_design.md`
- Docker containers (api, db, redis, worker, nginx)

**Step 14 — BE Tests Pass**
- รัน `pytest tests/be/` ทุก TC ต้อง green
- Allure report ไม่มี failure
- Code coverage ≥ 80%

**Step 15 — Build FE UI + Connect API**
- React + TypeScript + Vite
- Implement UI ตาม FE Design (Azure Studio Pro)
- Connect ทุก endpoint กับ BE API
- E2E flow ทดสอบได้

**Step 16 — FE + E2E Tests Pass**
- รัน `pytest tests/fe/` ทุก TC ต้อง green (Playwright)
- รัน `pytest tests/integration/` ทุก E2E flow ต้อง green
- Fallback locator report: ไม่มี XPath fallback ที่ยังค้างอยู่

**Step 17 — CI/CD Pipeline + Deploy**
- GitHub Actions workflow
- 2 environments: `dev` (auto-deploy on merge to main) + `prod` (manual approve)
- แยก domain เช่น `dev.studio.com` และ `studio.com`
- Secrets management per environment
- Docker build + push + deploy

**Step 18 — Scheduled Test Runs**
- Cron schedule รัน BE + FE tests อัตโนมัติ
- เช่น ทุกคืน 02:00 → รัน full test suite
- Notify ถ้า test fail (email / LINE / Slack)
