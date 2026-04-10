# FE Requirements Analysis
## Pila Studio Management — Web Application

> **Source:** `Requirement/studio-management/app-context.md` + `FE Design/` screens
> **Date:** 2026-04-05
> **Target Platform:** Desktop/Tablet first, responsive for tablet

---

## Design System Summary

| Token | Value | Usage |
|-------|-------|-------|
| Primary | `#162839` Deep Sea | Navigation, headers |
| Secondary | `#395f94` Steel Blue | Interactive elements |
| Accent | `#54b6b5` Muted Teal | CTAs, success states |
| Surface | `#f8fafb` Soft White | Canvas |
| Font Display | Manrope | Headlines |
| Font Body | Inter | Body text |

**Key Rules:**
- No 1px divider lines — use background tonal shifts instead
- Glassmorphism on floating elements (`backdrop-blur: 12px`)
- Ambient shadows only: `0px 20px 40px rgba(25,28,29,0.06)`
- Thai text line-height: 1.6× font size
- Generous whitespace — "if you think there's enough, add 20% more"

---

## Pages & Components

---

### AUTH — Login

**Route:** `/login`

**Components:**
- Email input field
- Password input field (masked)
- Submit button (primary CTA with gradient)
- Error message area

**States:**
- Default / Loading / Error (invalid credentials) / Success → redirect to PIN

**Business Rules:**
- No self-registration; users created by Branch Manager or Owner only
- On success → navigate to `/pin`

---

### AUTH — PIN Entry

**Route:** `/pin`

**Components:**
- 6-digit PIN input (numeric keypad or input)
- "Forgot PIN?" link
- Submit button

**States:**
- Default / Loading / Error (wrong PIN) / Expired (session > 5h)

**Business Rules:**
- PIN session expires every 5 hours; only PIN re-entry required (not full login)
- Forgot PIN → OTP sent to email → `/pin/reset`

---

### AUTH — PIN Reset (OTP)

**Route:** `/pin/reset`

**Components:**
- OTP input (from email)
- New PIN input
- Confirm PIN input
- Submit button

---

### LAYOUT — Sidebar Navigation

**Component:** `<Sidebar />`

**Menu Groups:**
1. **Overview** — Dashboard
2. **Operations** — Session Deduct, Booking/Schedule
3. **Records** — Customer, Order, Session Log, Trainer Training
4. **Management** — Trainer, Package, Caretaker, User
5. **System** — Permission, Branch Config, Activity Log, Settings
6. **Help** — Help Page

**States per menu item:** Default / Hover / Active

**Role-based visibility:**

| Role | Visible Menu Scope |
|------|--------------------|
| `developer` | All menus + partner switcher + branch switcher |
| `owner` | All menus within partner + branch switcher |
| `branch_master` | All menus within assigned branch |
| `admin` | Only menus permitted by permission matrix |
| `trainer` | Only menus permitted by permission matrix |

**Branch & Partner indicator:**
- Current active branch always shown in sidebar header
- `developer` and `owner` see a branch switcher dropdown
- `branch_master`, `admin`, `trainer` see branch name as static label (no switcher)

---

### DASHBOARD

**Route:** `/dashboard`

**Role-based content:**

| Role | Cards Shown |
|------|-------------|
| `trainer` | Hours trained (today/MTD), own customer count, own bookings |
| `admin` | Orders today (branch), sessions deducted today (branch) |
| `branch_master` | All orders (branch), revenue, breakdown by admin/trainer |
| `owner` | Branch master view + all branches + branch selector within partner |
| `developer` | Owner view + partner selector + cross-partner aggregate |

**Components:**
- Summary stat cards (icon + number + label + trend)
- Line/bar chart (revenue or sessions over time)
- Time range filter (Today / This Week / This Month / Custom)
- Branch selector (Owner only)

**States:** Loading skeleton / Populated / Empty / Error

---

### CUSTOMER MANAGEMENT

#### Customer List
**Route:** `/customers`

**Components:**
- Search bar (name, nickname, customer code)
- Filter chips: Branch / Status (Active/Inactive)
- Data table: Customer Code | Name | Nickname | Phone | Branch | Status | Actions
- "Add Customer" button (primary)
- Pagination

**States:** Loading / Populated / Empty / Search no results

#### Customer Form (Add/Edit)
**Route:** `/customers/new` | `/customers/:id/edit`

**Sections & Fields:**
1. **Branch & Code** — Branch selector (dropdown), Customer Code (auto-generated, read-only), Source Type (chip selector)
2. **Assignment** — Trainer (chip selector, filtered by branch), Caretaker (chip selector, filtered by branch)
3. **Identity** — First name, Last name, Nickname, Display name
4. **Contact** — Channel (Phone/LINE chip), Phone number, LINE ID, Email
5. **Status & Notes** — Status toggle (Active/Inactive), Notes (textarea)
6. **Profile** — Profile photo upload, Birthday (date picker), Is Duplicate flag (checkbox)

**Business Rules:**
- Customer code auto-generated: `[BranchPrefix]-[SourceCode][RunningNumber]`
- Trainer/Caretaker chip selectors must filter by the selected branch
- Display name auto-suggested from nickname

**States:** New form / Edit pre-filled / Saving / Validation error / Success

#### Customer Detail View
**Route:** `/customers/:id`

**Sections:**
- Profile header (photo, name, code, status badge)
- Contact info
- Assignment (trainer, caretaker)
- Order history table (linked)
- Remaining session hours (summary card)
- Edit / Delete buttons (role-gated)

---

### ORDER MANAGEMENT

#### Order List
**Route:** `/orders`

**Components:**
- Date range filter
- Branch filter
- Customer search/filter
- Data table: Date | Customer Code | Customer Name | Package | Hours | Payment | Branch | Actions
- "Add Order" button
- Outstanding balance badge on rows with unpaid balance

**States:** Loading / Populated / Empty / Filtered empty

#### Order Form (Add/Edit)
**Route:** `/orders/new` | `/orders/:id/edit`

**Sections & Fields:**
1. **Date** — Order date (date picker)
2. **Customer** — Customer dropdown (search by name/code), Trainer (chip, auto-filled from customer), Caretaker (chip, auto-filled)
3. **Package** — Package chip selector (active + branch-matched only), Hours (stepper), Bonus hours (stepper)
4. **Payment** — Payment method (Credit/Bank Transfer chip), Total price, Price per session, Installment plan, Outstanding balance
5. **Branch & Flags** — Branch selector, Renew flag (checkbox), Notes

**Business Rules:**
- Trainer and Caretaker auto-filled from customer profile (editable)
- Package selector filters: active status + branch match
- Receipt/Invoice email sent automatically on save

**States:** New / Edit / Saving / Validation error / Success

#### Order Detail View
**Route:** `/orders/:id`

**Sections:**
- Order header (date, customer, status)
- Package & hours summary
- Payment breakdown (installments, outstanding)
- Session usage history
- Receipt download / resend email buttons

---

### SESSION SYSTEM

#### Session Deduct
**Route:** `/sessions/deduct`

**Components:**
- Branch chip selector
- Customer search dropdown (shows name + code, NOT UUID — critical fix from old system)
- Deduct button
- Session deduction history table (Customer | Date | Hours deducted | Trainer | Remaining)

**States:** No customer selected / Customer selected / Deducting / Success / Error

#### Session Log
**Route:** `/sessions/log`

**Components:**
- Filter: Date range / Branch / Customer
- Data table: Timestamp | Customer Code | Customer Name | Transaction Type | Before | Amount | After | Actor
- Export button

#### Trainer Training Report
**Route:** `/sessions/trainer-report`

**Components:**
- Quick filter buttons: Today / This Month
- Date range picker
- Branch selector + Trainer selector
- Summary cards: Total hours, Sessions count
- Training history table: Date/Time | Trainer | Customer | Hours

---

### TRAINER MANAGEMENT

#### Trainer List
**Route:** `/trainers`

**Components:**
- Branch filter
- Status filter (Active/Inactive)
- Card grid or table view toggle
- Card: Profile photo, Name, Branch badge, Status, Edit button

#### Trainer Form
**Route:** `/trainers/new` | `/trainers/:id/edit`

**Fields:** Name, Display name (auto), Status, Email, Profile photo upload, Branch (multi or single)

---

### PACKAGE MANAGEMENT

#### Package List
**Route:** `/packages`

**Components:**
- Filter: Type (Sale/Pre-sale) / Branch / Status (Active/Inactive/Expired)
- Data table: Name | Hours | Type | Branch | Price | Status | Active Period | Actions
- Status badges: Active (teal) / Inactive (grey) / Expired (red)
- "Add Package" button

#### Package Form
**Route:** `/packages/new` | `/packages/:id/edit`

**Fields:** Package name, Hours (stepper), Type (Sale/Pre-sale), Price, Branch scope (All / Selected), Active period (date range, optional), Status toggle

---

### BOOKING / SCHEDULE

**Route:** `/booking`

**Components:**
- View toggle: 3-day (default) / Full week (7 days)
- Previous / Next navigation
- Timetable grid (30-min slots, columns = days, rows = time)
- Color coding: Staff schedule (blue) / Customer booking (teal) / Pending (amber)
- Glassmorphism on booked slots
- Click slot → popup form (add booking/schedule)
- Booking table view (separate tab)
- Role-based actions: Trainer (own schedule only), Admin (all)

**Booking Popup Fields:** Customer, Trainer, Date/Time, Duration, Status

**Status flow:** Pending → Confirmed → Cancelled (Admin/Owner only)

**Confirm flow:** Confirm → if LINE → "Notify customer?" prompt

---

### USER MANAGEMENT

**Route:** `/users`

**Components:**
- Filter: Role / Branch / Status
- Data table grouped by Active/Inactive: Name | Role badge | Branch | Actions
- "Add User" button (visible to: `developer`, `owner`, `branch_master`)
- Slide-out detail panel (from FE design `user_management_slide_out_details`)

**Form Fields:** Username, Password (masked), Role (dropdown), Branch

**Business Rules:**
- `developer` can create any role across any partner/branch
- `owner` can create `branch_master`, `admin`, `trainer` within own partner
- `branch_master` can only create `admin` and `trainer` within own branch
- Role dropdown options are filtered based on the creator's role (cannot create equal or higher role)
- Role badge colors: `developer`=purple, `owner`=deep-sea `#162839`, `branch_master`=steel-blue `#395f94`, `admin`=teal `#54b6b5`, `trainer`=grey

---

### PERMISSION MANAGEMENT

**Route:** `/permissions`

**Components:**
- Permission matrix: Module rows × Role columns (columns vary by the logged-in role's hierarchy)
- Toggle switches (not checkboxes) for each cell
- Sections: View / Create / Edit / Delete per module

**Matrix columns visible per logged-in role:**

| Logged-in Role | Columns shown in matrix |
|----------------|------------------------|
| `developer` | owner, branch_master, admin, trainer |
| `owner` | branch_master, admin, trainer |
| `branch_master` | admin, trainer |
| `admin` | — (no access to permission page) |
| `trainer` | — (no access to permission page) |

**Business Rules:**
- Each role can only configure roles that are **below** them in the hierarchy
- A role's own permissions are set by whoever is above them — never editable by that role itself
- `admin` and `trainer` have no access to the permission page at all
- FE hides/disables UI elements based on the resolved permission; BE guards every API endpoint independently
- Feature toggle (module on/off) is a separate control above the matrix — visible to `developer`, `owner`, `branch_master`

---

### BRANCH CONFIG

**Route:** `/settings/branches`

**Components:**
- Branch list table: Name | Prefix | Source Types | Operating Hours | Actions
- Edit form per branch
- Source Type sub-form: Label, Code
- Operating hours picker (open/close time per branch)

---

### SETTINGS

**Route:** `/settings`

**Components:**
- Language toggle (Thai / English)
- Dark mode toggle
- Google Account connection button + status
- Google Drive storage gauge (X GB / Y GB)
- Profile section (Name, Role, Branch — read-only)

---

### ACTIVITY LOG

**Route:** `/activity-log`

**Components:**
- Filters: Date range / User / Action type / Branch
- Timeline or table view: Timestamp | Actor | Action | Target | Changes (before/after)

---

### CARETAKER MANAGEMENT

**Route:** `/caretakers`

**Components:**
- Branch filter
- List grouped by branch (or table)
- Context menu per row (Edit / Deactivate)
- Form: Name, Email, Branch, Status

---

### HELP

**Route:** `/help`

**Components:**
- Role-based manual sections (only show features user can access)
- Search within manual
- LINE QR codes: Developer contact + per-branch group chat
- Expandable FAQ sections

---

## Cross-Cutting FE Requirements

| # | Requirement |
|---|-------------|
| CR-01 | All dropdowns showing people/customers must display Name, never UUID |
| CR-02 | Chip selectors for Trainer/Caretaker must filter by selected Branch |
| CR-03 | Sidebar shows only menu items the current role has permission to access |
| CR-04 | Feature Toggle: show overlay "ฟีเจอร์นี้ไม่พร้อมใช้งาน" when module disabled |
| CR-05 | All forms must have loading state, success toast, and error message |
| CR-06 | Tables must support pagination, sorting, and keyword search |
| CR-07 | Thai language support with line-height 1.6× for Thai characters |
| CR-08 | Responsive: functional on tablet (≥768px), optimized for desktop (≥1280px) |
| CR-09 | Active branch always visible in sidebar |
| CR-10 | All destructive actions require confirmation dialog |
