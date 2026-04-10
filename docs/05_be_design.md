# BE Design — Studio Management
## Version 1.2 | 2026-04-08
### Stack: Python (FastAPI) + PostgreSQL + Docker

### Changelog v1.2
- login_attempts แยกเป็น table ของตัวเอง (แก้ race condition multi-device)
- Rename: Session → Customer Hour ทุกที่ (tables, API endpoints, enums)
- payment_method เปลี่ยนเป็น enum UPPERCASE
- Enum ทุกตัวใช้ UPPERCASE
- actor_id → user_id ใน customer_hour_logs และ activity_logs (naming consistency)
- bookings เพิ่ม caretaker_id
- permission_matrix + feature_toggles เปลี่ยน module → feature_name
- user_preferences language เปลี่ยนเป็น LANGUAGE_ENUM
- เพิ่ม Auth email endpoints (password forgot/reset/change)
- เพิ่ม password_reset_tokens table
- เพิ่ม Internal developer-only endpoints (/internal/*)
- Auth flow: JWT ออกหลัง PIN verify เท่านั้น
- Permission API → owner+, Activity Log API → branch_master+

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                        Client (FE)                       │
│              React Web App (Desktop/Tablet)              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────┐
│                    Nginx (Reverse Proxy)                  │
│              SSL Termination + Static Serve               │
└──────┬───────────────────────────────────┬──────────────┘
       │ /api/*                            │ /*
┌──────▼──────────┐               ┌────────▼──────────────┐
│   API Service   │               │    FE Static Files     │
│  FastAPI + Uvicorn│             │   (Nginx serve)        │
│   Port: 8000    │               └───────────────────────┘
└──────┬──────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│                    PostgreSQL Service                     │
│                      Port: 5432                          │
└──────────────────────────────────────────────────────────┘
       │
┌──────▼──────────┐    ┌────────────────────┐
│  Redis Service  │    │   Worker Service   │
│  (Cache + Rate  │    │ (Celery — Email,   │
│   Limiting)     │    │  Google Drive)     │
│   Port: 6379    │    └────────────────────┘
└─────────────────┘
```

### Services (Docker Containers)
| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `api` | `studio-api` | 8000 | FastAPI application |
| `db` | `postgres:16` | 5432 | PostgreSQL database |
| `redis` | `redis:7-alpine` | 6379 | Cache + rate limiting + session store |
| `worker` | `studio-worker` | — | Celery async tasks (email, Google Drive) |
| `nginx` | `nginx:alpine` | 80/443 | Reverse proxy + SSL |

---

## 2. Folder Structure

```
studio-management/
├── docker-compose.yml              # All services orchestration
├── docker-compose.dev.yml          # Dev overrides (hot reload, debug)
├── .env.example                    # Template for environment variables
├── .env                            # Actual secrets (gitignored)
│
├── api/                            # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Settings from env vars (pydantic BaseSettings)
│   ├── database.py                 # SQLAlchemy engine + session factory
│   │
│   ├── models/                     # SQLAlchemy ORM models (DB tables)
│   │   ├── __init__.py
│   │   ├── user.py                 # User, role, PIN, user_sessions
│   │   ├── login_attempt.py        # LoginAttempt (แยกออกมาแก้ race condition multi-device)
│   │   ├── branch.py               # Branch, source_type
│   │   ├── customer.py             # Customer, customer_code_counter
│   │   ├── trainer.py              # Trainer
│   │   ├── caretaker.py            # Caretaker
│   │   ├── package.py              # Package, package_branch_scope
│   │   ├── order.py                # Order, order_payment
│   │   ├── customer_hour.py        # CustomerHourBalance, CustomerHourLog (เดิม: session.py)
│   │   ├── booking.py              # Booking, cancel_policy
│   │   ├── permission.py           # PermissionMatrix, feature_toggle
│   │   ├── activity_log.py         # ActivityLog
│   │   └── google_integration.py  # GoogleToken
│   │
│   ├── schemas/                    # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── branch.py
│   │   ├── customer.py
│   │   ├── trainer.py
│   │   ├── caretaker.py
│   │   ├── package.py
│   │   ├── order.py
│   │   ├── customer_hour.py        # (เดิม: session.py)
│   │   ├── booking.py
│   │   ├── user.py
│   │   ├── permission.py
│   │   ├── dashboard.py
│   │   ├── activity_log.py
│   │   └── common.py               # Pagination, error responses
│   │
│   ├── routers/                    # API route handlers (one file per module)
│   │   ├── __init__.py
│   │   ├── auth.py                 # /auth/*
│   │   ├── internal.py             # /internal/* (developer-only, no UI)
│   │   ├── branches.py             # /branches/*
│   │   ├── customers.py            # /customers/*
│   │   ├── trainers.py             # /trainers/*
│   │   ├── caretakers.py           # /caretakers/*
│   │   ├── packages.py             # /packages/*
│   │   ├── orders.py               # /orders/*
│   │   ├── customer_hours.py       # /customer-hours/* (เดิม: sessions.py)
│   │   ├── bookings.py             # /bookings/*
│   │   ├── users.py                # /users/*
│   │   ├── permissions.py          # /permissions/*
│   │   ├── dashboard.py            # /dashboard/*
│   │   ├── activity_log.py         # /activity-log/*
│   │   ├── signature_print.py      # /signature-print/*
│   │   ├── settings.py             # /settings/*
│   │   └── help.py                 # /help/*
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Login, PIN, OTP, token management
│   │   ├── customer_service.py     # Customer CRUD + code generation
│   │   ├── order_service.py        # Order CRUD + hour allocation
│   │   ├── customer_hour_service.py # Deduct, adjust, log (เดิม: session_service.py)
│   │   ├── booking_service.py      # Booking lifecycle + cancel policy
│   │   ├── permission_service.py   # Matrix check + feature toggle
│   │   ├── dashboard_service.py    # Aggregation queries per role
│   │   ├── google_service.py       # Google Drive + Sheets integration
│   │   ├── email_service.py        # Email sending (OTP, receipt, password reset)
│   │   └── activity_log_service.py # Create log entries
│   │
│   ├── dependencies/               # FastAPI dependency injection
│   │   ├── __init__.py
│   │   ├── auth.py                 # get_current_user, require_pin_verified
│   │   ├── permissions.py          # require_roles(), check_feature_toggle()
│   │   └── branch_scope.py         # apply_branch_filter() per role
│   │
│   ├── middleware/                 # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── rate_limiter.py         # Redis-based rate limiting
│   │   └── activity_logger.py      # Auto-log write operations
│   │
│   ├── tasks/                      # Celery async tasks
│   │   ├── __init__.py
│   │   ├── email_tasks.py          # Send OTP, receipt, invoice
│   │   └── drive_tasks.py          # Generate Google Sheet, upload
│   │
│   ├── utils/                      # Shared utilities
│   │   ├── __init__.py
│   │   ├── security.py             # bcrypt hash, JWT encode/decode
│   │   ├── pagination.py           # Pagination helper
│   │   └── validators.py           # Custom validators (email, phone, etc.)
│   │
│   └── migrations/                 # Alembic DB migrations
│       ├── env.py
│       ├── alembic.ini
│       └── versions/
│           └── 001_initial_schema.py
│
├── worker/                         # Celery worker (shares code with api/)
│   ├── Dockerfile
│   └── celery_app.py               # Celery configuration
│
└── nginx/
    ├── Dockerfile
    └── nginx.conf                  # Reverse proxy configuration
```

---

## 3. Database Schema (ERD)

### 3.0 Enums
```sql
-- Enum ทุกตัวใช้ UPPERCASE เสมอ (naming consistency rule)

CREATE TYPE role_enum AS ENUM ('DEVELOPER', 'OWNER', 'BRANCH_MASTER', 'ADMIN', 'TRAINER');
CREATE TYPE status_enum AS ENUM ('ACTIVE', 'INACTIVE');
CREATE TYPE payment_method_enum AS ENUM ('CREDIT', 'BANK_TRANSFER');
CREATE TYPE sale_type_enum AS ENUM ('SALE', 'PRE_SALE');
CREATE TYPE branch_scope_enum AS ENUM ('ALL', 'SELECTED');
CREATE TYPE booking_type_enum AS ENUM ('CUSTOMER', 'STAFF_SCHEDULE');
CREATE TYPE booking_source_enum AS ENUM ('INTERNAL', 'EXTERNAL_API');
CREATE TYPE booking_status_enum AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED');
CREATE TYPE hour_transaction_type_enum AS ENUM ('PURCHASED', 'HOUR_DEDUCT', 'HOUR_ADJUST', 'NEW_CUSTOMER');
CREATE TYPE permission_action_enum AS ENUM ('VIEW', 'CREATE', 'EDIT', 'DELETE');
CREATE TYPE language_enum AS ENUM ('TH', 'EN');
CREATE TYPE contact_channel_enum AS ENUM ('PHONE', 'LINE');
CREATE TYPE qr_type_enum AS ENUM ('DEVELOPER', 'BRANCH');
```

---

### 3.1 Core Tables

#### `partners`
```sql
CREATE TABLE partners (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

#### `branches`
```sql
CREATE TABLE branches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id      UUID NOT NULL REFERENCES partners(id),
    name            VARCHAR(255) NOT NULL,
    prefix          VARCHAR(10) NOT NULL UNIQUE,  -- e.g. "BPY"
    opening_time    TIME NOT NULL DEFAULT '09:00',
    closing_time    TIME NOT NULL DEFAULT '21:00',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `source_types`
```sql
CREATE TABLE source_types (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id   UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    label       VARCHAR(100) NOT NULL,   -- e.g. "Page"
    code        VARCHAR(20) NOT NULL,    -- e.g. "MKT"
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(branch_id, code)              -- code must be unique per branch
);
```

#### `customer_code_counters`
```sql
CREATE TABLE customer_code_counters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id       UUID NOT NULL REFERENCES branches(id),
    source_type_id  UUID NOT NULL REFERENCES source_types(id),
    last_number     INTEGER NOT NULL DEFAULT 0,
    UNIQUE(branch_id, source_type_id)   -- one counter per branch+source combo
);
```

#### `users`
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id      UUID NOT NULL REFERENCES partners(id),
    branch_id       UUID REFERENCES branches(id),   -- NULL for owner/developer
    username        VARCHAR(100) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,           -- bcrypt hash
    pin_hash        VARCHAR(255),                    -- bcrypt hash of PIN
    role            role_enum NOT NULL,              -- UPPERCASE enum
    is_active       BOOLEAN DEFAULT TRUE,
    pin_locked      BOOLEAN DEFAULT FALSE,
    pin_attempts    INTEGER DEFAULT 0,               -- reset เมื่อ PIN verify สำเร็จ
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
    -- login_attempts ย้ายออกไปเป็น table แยก (login_attempts) แก้ race condition multi-device
);
```

#### `login_attempts`
```sql
-- แยก login_attempts ออกจาก users table
-- เหตุผล: ถ้าเก็บใน users.login_attempts และมีหลาย device login พร้อมกัน
-- จะเกิด race condition ทำให้ count ไม่ถูกต้อง
-- การแยกเป็น table ทำให้ INSERT แต่ละ attempt อย่าง atomic และนับได้แม่นยำ
CREATE TABLE login_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,    -- เก็บ email ด้วย เผื่อ user ไม่มีในระบบ
    ip_address      VARCHAR(45),
    success         BOOLEAN NOT NULL DEFAULT FALSE,
    attempted_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_time ON login_attempts(attempted_at DESC);
```

#### `pin_otp`
```sql
CREATE TABLE pin_otp (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    otp_hash    VARCHAR(255) NOT NULL,   -- hashed OTP
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

#### `password_reset_tokens`
```sql
-- ใช้สำหรับ reset password ผ่าน email
-- แยกจาก pin_otp เพราะ flow และ expiry ต่างกัน
CREATE TABLE password_reset_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL,   -- hashed reset token
    expires_at  TIMESTAMPTZ NOT NULL,   -- หมดอายุเร็วกว่า login session (เช่น 15 นาที)
    used        BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pwd_reset_user ON password_reset_tokens(user_id);
```

#### `user_sessions`
```sql
-- JWT จริงจะออกให้หลังจาก PIN verify สำเร็จเท่านั้น
-- ก่อน PIN verify: ใช้ temporary_token (ไม่ใช่ JWT) เพื่อระบุตัวตนเท่านั้น
-- หลัง PIN verify: ออก JWT จริง → ใช้ได้กับทุก protected API
CREATE TABLE user_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    temporary_token_hash VARCHAR(255),             -- token ชั่วคราวหลัง login (ก่อน PIN)
    access_token_hash   VARCHAR(255),              -- JWT จริง (ออกหลัง PIN verify สำเร็จ)
    pin_verified_at     TIMESTAMPTZ,               -- NULL = PIN ยังไม่ผ่าน → JWT ยังไม่ออก
    pin_expires_at      TIMESTAMPTZ,               -- PIN session expiry (5h นับจาก pin_verified_at)
    login_expires_at    TIMESTAMPTZ NOT NULL,      -- Full login session expiry
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.2 Customer Tables

#### `customers`
```sql
CREATE TABLE customers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id          UUID NOT NULL REFERENCES partners(id),
    branch_id           UUID NOT NULL REFERENCES branches(id),
    source_type_id      UUID NOT NULL REFERENCES source_types(id),
    customer_code       VARCHAR(50) NOT NULL UNIQUE,  -- e.g. BPY-MKT001
    first_name          VARCHAR(255) NOT NULL,
    last_name           VARCHAR(255),
    nickname            VARCHAR(100),
    display_name        VARCHAR(255),
    contact_channel     contact_channel_enum,             -- 'PHONE' | 'LINE'
    phone               VARCHAR(20),
    line_id             VARCHAR(100),
    email               VARCHAR(255),
    status              status_enum NOT NULL DEFAULT 'ACTIVE',
    notes               TEXT,
    profile_photo_url   VARCHAR(500),
    birthday            DATE,
    is_duplicate        BOOLEAN DEFAULT FALSE,
    trainer_id          UUID REFERENCES trainers(id),    -- assigned trainer
    caretaker_id        UUID REFERENCES caretakers(id),  -- assigned caretaker
    created_by          UUID REFERENCES users(id),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_branch ON customers(branch_id);
CREATE INDEX idx_customers_partner ON customers(partner_id);
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_status ON customers(status);
```

---

### 3.3 Trainer & Caretaker Tables

#### `trainers`
```sql
CREATE TABLE trainers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id           UUID NOT NULL REFERENCES branches(id),
    name                VARCHAR(255) NOT NULL,
    display_name        VARCHAR(255),               -- auto: "Name:Branch"
    email               VARCHAR(255),
    profile_photo_url   VARCHAR(500),
    status              status_enum NOT NULL DEFAULT 'ACTIVE',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `caretakers`
```sql
CREATE TABLE caretakers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id   UUID NOT NULL REFERENCES branches(id),
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255),
    status      status_enum NOT NULL DEFAULT 'ACTIVE',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.4 Package Tables

#### `packages`
```sql
CREATE TABLE packages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id      UUID NOT NULL REFERENCES partners(id),
    name            VARCHAR(255) NOT NULL,
    hours           INTEGER NOT NULL CHECK (hours > 0),
    sale_type       sale_type_enum NOT NULL,         -- 'SALE' | 'PRE_SALE'
    price           NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    branch_scope    branch_scope_enum NOT NULL DEFAULT 'ALL',  -- 'ALL' | 'SELECTED'
    active_from     DATE,                   -- NULL = always active
    active_until    DATE,                   -- NULL = never expires
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `package_branch_scopes`
```sql
-- Only used when package.branch_scope = 'selected'
CREATE TABLE package_branch_scopes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id  UUID NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
    branch_id   UUID NOT NULL REFERENCES branches(id),
    UNIQUE(package_id, branch_id)
);
```

---

### 3.5 Order & Payment Tables

#### `orders`
```sql
CREATE TABLE orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id          UUID NOT NULL REFERENCES partners(id),
    branch_id           UUID NOT NULL REFERENCES branches(id),
    customer_id         UUID NOT NULL REFERENCES customers(id),
    package_id          UUID NOT NULL REFERENCES packages(id),
    trainer_id          UUID REFERENCES trainers(id),
    caretaker_id        UUID REFERENCES caretakers(id),
    order_date          DATE NOT NULL,
    hours               INTEGER NOT NULL CHECK (hours >= 0),
    bonus_hours         INTEGER NOT NULL DEFAULT 0 CHECK (bonus_hours >= 0),
    total_hours         INTEGER GENERATED ALWAYS AS (hours + bonus_hours) STORED,
    payment_method      payment_method_enum NOT NULL,    -- 'CREDIT' | 'BANK_TRANSFER'
    total_price         NUMERIC(10,2) NOT NULL CHECK (total_price >= 0),
    price_per_session   NUMERIC(10,2),
    paid_amount         NUMERIC(10,2) NOT NULL DEFAULT 0,
    outstanding         NUMERIC(10,2) GENERATED ALWAYS AS (total_price - paid_amount) STORED,
    has_outstanding     BOOLEAN GENERATED ALWAYS AS (total_price > paid_amount) STORED,
    is_renewal          BOOLEAN DEFAULT FALSE,
    renewed_from_id     UUID REFERENCES orders(id),  -- linked previous order if renewal
    notes               TEXT,
    notes2              TEXT,
    created_by          UUID REFERENCES users(id),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_branch ON orders(branch_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date DESC);
CREATE INDEX idx_orders_outstanding ON orders(has_outstanding) WHERE has_outstanding = TRUE;
```

#### `order_payments`
```sql
CREATE TABLE order_payments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount              NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    paid_at             DATE NOT NULL,
    note                TEXT,
    recorded_by         UUID REFERENCES users(id),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.6 Customer Hour Tables
*(เดิมชื่อ Session Tables — เปลี่ยนชื่อให้สื่อความหมายชัดเจนขึ้น)*

#### `customer_hour_balances`
```sql
-- เดิมชื่อ: session_balances
CREATE TABLE customer_hour_balances (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID NOT NULL UNIQUE REFERENCES customers(id),
    remaining       INTEGER NOT NULL DEFAULT 0 CHECK (remaining >= 0),  -- DB constraint: never negative
    last_updated_by UUID REFERENCES users(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `customer_hour_logs`
```sql
-- เดิมชื่อ: session_transaction_logs
-- actor_id → user_id (naming consistency กับ tables อื่นๆ)
CREATE TABLE customer_hour_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id),
    branch_id           UUID REFERENCES branches(id),
    trainer_id          UUID REFERENCES trainers(id),
    transaction_type    hour_transaction_type_enum NOT NULL, -- PURCHASED|HOUR_DEDUCT|HOUR_ADJUST|NEW_CUSTOMER
    before_amount       INTEGER NOT NULL,
    amount              INTEGER NOT NULL,         -- positive=add, negative=deduct
    after_amount        INTEGER NOT NULL,
    reason              TEXT,
    user_id             UUID REFERENCES users(id),  -- user ที่ทำ action (เดิม: actor_id)
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_hour_log_customer ON customer_hour_logs(customer_id);
CREATE INDEX idx_hour_log_created ON customer_hour_logs(created_at DESC);
```

---

### 3.7 Booking Tables

#### `bookings`
```sql
CREATE TABLE bookings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id       UUID NOT NULL REFERENCES branches(id),
    customer_id     UUID REFERENCES customers(id),          -- NULL for staff schedule only
    trainer_id      UUID REFERENCES trainers(id),
    caretaker_id    UUID REFERENCES caretakers(id),         -- ผู้ดูแลลูกค้าในการนัดนี้
    booking_type    booking_type_enum NOT NULL DEFAULT 'CUSTOMER',  -- 'CUSTOMER' | 'STAFF_SCHEDULE'
    booking_source  booking_source_enum NOT NULL DEFAULT 'INTERNAL', -- 'INTERNAL' | 'EXTERNAL_API'
    start_time      TIMESTAMPTZ NOT NULL,
    end_time        TIMESTAMPTZ NOT NULL,
    status          booking_status_enum NOT NULL DEFAULT 'PENDING',  -- 'PENDING'|'CONFIRMED'|'CANCELLED'
    line_notified   BOOLEAN DEFAULT FALSE,
    hour_returned   BOOLEAN DEFAULT FALSE,              -- เดิม: session_returned
    notes           TEXT,
    confirmed_by    UUID REFERENCES users(id),
    confirmed_at    TIMESTAMPTZ,
    cancelled_by    UUID REFERENCES users(id),
    cancelled_at    TIMESTAMPTZ,
    cancel_reason   TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bookings_branch ON bookings(branch_id);
CREATE INDEX idx_bookings_trainer ON bookings(trainer_id);
CREATE INDEX idx_bookings_start ON bookings(start_time);
CREATE INDEX idx_bookings_status ON bookings(status);
```

#### `cancel_policies`
```sql
CREATE TABLE cancel_policies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id       UUID NOT NULL UNIQUE REFERENCES branches(id),
    hours_before    INTEGER NOT NULL DEFAULT 24,     -- min hours before booking to cancel
    return_hour     BOOLEAN NOT NULL DEFAULT TRUE,   -- return customer hour balance on cancel (เดิม: return_session)
    updated_by      UUID REFERENCES users(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.8 Permission Tables

#### `permission_matrix`
```sql
CREATE TABLE permission_matrix (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id       UUID REFERENCES branches(id),  -- NULL = applies to all branches (for owner level)
    role            role_enum NOT NULL,             -- which role this permission applies to
    feature_name    VARCHAR(100) NOT NULL,          -- e.g. 'customer', 'order', 'booking' (เดิม: module)
    action          permission_action_enum NOT NULL, -- 'VIEW'|'CREATE'|'EDIT'|'DELETE'
    is_allowed      BOOLEAN NOT NULL DEFAULT TRUE,
    updated_by      UUID REFERENCES users(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(branch_id, role, feature_name, action)
);
```

#### `feature_toggles`
```sql
CREATE TABLE feature_toggles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id      UUID NOT NULL REFERENCES partners(id),
    feature_name    VARCHAR(100) NOT NULL,          -- e.g. 'booking', 'tax_accounting' (เดิม: module)
    is_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    updated_by      UUID REFERENCES users(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(partner_id, feature_name)
);
```

---

### 3.9 Activity Log Table

#### `activity_logs`
```sql
CREATE TABLE activity_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id      UUID REFERENCES partners(id),
    branch_id       UUID REFERENCES branches(id),
    user_id         UUID REFERENCES users(id),      -- user ที่ทำ action (เดิม: actor_id)
    action          VARCHAR(100) NOT NULL,           -- e.g. 'customer.create', 'customer_hour.deduct'
    target_type     VARCHAR(50),                     -- e.g. 'customer', 'order', 'booking'
    target_id       UUID,                            -- ID of the affected record
    changes         JSONB,                           -- before/after snapshot
    ip_address      VARCHAR(45),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_branch ON activity_logs(branch_id);
CREATE INDEX idx_activity_user ON activity_logs(user_id);     -- เดิม: idx_activity_actor
CREATE INDEX idx_activity_action ON activity_logs(action);
CREATE INDEX idx_activity_created ON activity_logs(created_at DESC);
```

---

### 3.10 Google Integration Table

#### `google_tokens`
```sql
CREATE TABLE google_tokens (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    connected_email     VARCHAR(255) NOT NULL,
    access_token        TEXT NOT NULL,           -- encrypted at rest
    refresh_token       TEXT NOT NULL,           -- encrypted at rest
    token_expires_at    TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `signature_print_files`
```sql
CREATE TABLE signature_print_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID NOT NULL REFERENCES orders(id),
    generated_by    UUID REFERENCES users(id),
    file_url        VARCHAR(500) NOT NULL,        -- Google Sheets shareable link
    file_id         VARCHAR(255) NOT NULL,        -- Google Drive file ID
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.11 User Settings Table

#### `user_preferences`
```sql
CREATE TABLE user_preferences (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    language    language_enum NOT NULL DEFAULT 'TH',  -- 'TH' | 'EN' (เดิม: VARCHAR)
    dark_mode   BOOLEAN DEFAULT FALSE,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.12 Help Content Table

#### `help_content`
```sql
CREATE TABLE help_content (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_key     VARCHAR(100) NOT NULL,          -- e.g. 'customer_management'
    title_th        VARCHAR(255) NOT NULL,
    title_en        VARCHAR(255),
    content_th      TEXT,
    content_en      TEXT,
    visible_to      VARCHAR[]  NOT NULL,             -- roles that can see this section
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `line_qr_codes`
```sql
CREATE TABLE line_qr_codes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            qr_type_enum NOT NULL,           -- 'DEVELOPER' | 'BRANCH'
    branch_id       UUID REFERENCES branches(id),    -- NULL for developer QR
    qr_image_url    VARCHAR(500) NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. API Endpoints Specification

### 4.1 Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/login` | None | Email + password → temporary token (ยังไม่ใช่ JWT) |
| POST | `/auth/pin/verify` | Temp token | Verify PIN → **ออก JWT จริง** |
| POST | `/auth/pin/forgot` | None | Request OTP to email |
| POST | `/auth/pin/reset` | None | Reset PIN with OTP |
| POST | `/auth/password/forgot` | None | Request password reset email |
| POST | `/auth/password/reset` | None | Reset password with token from email |
| POST | `/auth/password/change` | JWT + PIN | Change password (while logged in) |
| POST | `/auth/logout` | JWT + PIN | Invalidate session |
| GET | `/auth/me` | JWT + PIN | Get current user profile |

### 4.1b Internal (Developer-only)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/internal/assign-password/:user_id` | Developer API Key | Force-assign new password |
| POST | `/internal/assign-pin/:user_id` | Developer API Key | Force-assign new PIN + unlock |

> ⚠️ `/internal/*` endpoints: ไม่มี UI, ไม่มี role ปกติเข้าถึงได้, ใช้ Developer API Key เท่านั้น

### 4.2 Branches
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/branches` | JWT + PIN | List branches (role-scoped) |
| POST | `/branches` | owner+ | Create branch |
| GET | `/branches/:id` | JWT + PIN | Get branch detail |
| PUT | `/branches/:id` | owner+ | Update branch |
| DELETE | `/branches/:id` | owner+ | Delete branch (409 if has customers) |
| GET | `/branches/:id/source-types` | JWT + PIN | List source types for branch |
| POST | `/branches/:id/source-types` | owner+ | Add source type |
| PUT | `/branches/:id/source-types/:stid` | owner+ | Update source type |

### 4.3 Customers
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/customers` | JWT + PIN | List customers (paginated, role-scoped) |
| POST | `/customers` | admin+ | Create customer |
| GET | `/customers/:id` | JWT + PIN | Get customer detail |
| PUT | `/customers/:id` | admin+ | Update customer |
| DELETE | `/customers/:id` | owner/branch_master | Delete customer |

**Query Params (GET /customers):** `page`, `page_size`, `search`, `branch_id`, `status`, `sort_by`, `sort_dir`

### 4.4 Trainers
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/trainers` | JWT + PIN | List trainers (role-scoped) |
| POST | `/trainers` | admin+ | Create trainer |
| GET | `/trainers/:id` | JWT + PIN | Get trainer detail |
| PUT | `/trainers/:id` | admin+ | Update trainer |
| DELETE | `/trainers/:id` | admin+ | Delete trainer (409 if active customers/bookings) |

### 4.5 Caretakers
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/caretakers` | JWT + PIN | List caretakers (role-scoped) |
| POST | `/caretakers` | admin+ | Create caretaker |
| GET | `/caretakers/:id` | JWT + PIN | Get caretaker detail |
| PUT | `/caretakers/:id` | admin+ | Update caretaker |
| DELETE | `/caretakers/:id` | admin+ | Delete caretaker |

### 4.6 Packages
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/packages` | JWT + PIN | List packages |
| POST | `/packages` | owner+ | Create package |
| GET | `/packages/:id` | JWT + PIN | Get package detail |
| PUT | `/packages/:id` | owner+ | Update package |
| DELETE | `/packages/:id` | owner+ | Delete (409 if in active orders) |

**Query Params (GET /packages):** `active_only`, `branch_id`, `type`, `status`

### 4.7 Orders
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/orders` | JWT + PIN | List orders (role-scoped, paginated) |
| POST | `/orders` | admin+ | Create order |
| GET | `/orders/:id` | JWT + PIN | Get order detail with payment breakdown |
| PUT | `/orders/:id` | admin+ | Update order |
| DELETE | `/orders/:id` | owner+ | Delete order |
| POST | `/orders/:id/payments` | admin+ | Record installment payment |
| GET | `/orders/:id/payments` | JWT + PIN | Get payment history |
| POST | `/orders/:id/receipt` | admin+ | Send receipt email |

**Query Params (GET /orders):** `start_date`, `end_date`, `branch_id`, `customer_id`, `has_outstanding`

### 4.8 Customer Hours
*(เดิมชื่อ Sessions — เปลี่ยนชื่อให้ consistent กับ DB tables)*
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/customer-hours/deduct` | admin/trainer+ | Deduct 1 hour from customer |
| PUT | `/customer-hours/adjust` | admin+ | Manual adjust hour balance |
| GET | `/customer-hours/remaining/:customer_id` | JWT + PIN | Get customer's remaining balance |
| GET | `/customer-hours/log` | JWT + PIN | Hour transaction history |
| GET | `/customer-hours/trainer-report` | JWT + PIN | Trainer training summary |

**Query Params (GET /customer-hours/log):** `customer_id`, `branch_id`, `start_date`, `end_date`, `transaction_type`

**Query Params (GET /customer-hours/trainer-report):** `trainer_id`, `branch_id`, `start_date`, `end_date`

### 4.9 Bookings
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/bookings` | JWT + PIN | List bookings (role-scoped) |
| POST | `/bookings` | admin/trainer+ | Create booking or staff schedule |
| GET | `/bookings/:id` | JWT + PIN | Get booking detail |
| PUT | `/bookings/:id` | admin+ | Update booking |
| DELETE | `/bookings/:id` | admin+ | Cancel booking |
| PUT | `/bookings/:id/confirm` | admin+ | Confirm pending booking |
| POST | `/bookings/external` | API Key | External booking request |
| GET | `/settings/cancel-policy` | JWT + PIN | Get cancel policy |
| PUT | `/settings/cancel-policy` | owner+ | Update cancel policy |

**Query Params (GET /bookings):** `start_date`, `end_date`, `trainer_id`, `branch_id`, `status`

### 4.10 Users
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users` | branch_master+ | List users (role-scoped) |
| POST | `/users` | branch_master+ | Create user |
| GET | `/users/:id` | branch_master+ | Get user detail |
| PUT | `/users/:id` | branch_master+ | Update user info |
| PUT | `/users/:id/role` | owner/developer | Change user role |
| DELETE | `/users/:id` | branch_master+ | Deactivate user |

### 4.11 Permissions
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/permissions` | owner+ | Get permission matrix |
| PUT | `/permissions` | owner+ | Update permission matrix |
| GET | `/permissions/feature-toggles` | owner+ | Get feature toggle states |
| PUT | `/permissions/feature-toggles` | owner+ | Update feature toggle |

### 4.12 Dashboard
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dashboard` | JWT + PIN | Get dashboard data (role-based) |

**Query Params:** `range` (today/week/month/custom), `branch_id`, `start_date`, `end_date`

### 4.13 Activity Log
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/activity-log` | branch_master+ | Get activity logs (role-scoped) |

**Query Params:** `start_date`, `end_date`, `user_id`, `action`, `branch_id`

### 4.14 Signature Print
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/signature-print/generate` | admin+ | Generate Google Sheet for order |
| GET | `/signature-print/list` | admin+ | List generated files |
| GET | `/signature-print/storage` | admin+ | Get Google Drive storage info |

### 4.15 Settings
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/settings` | JWT + PIN | Get user preferences |
| PUT | `/settings` | JWT + PIN | Update language/dark mode |
| POST | `/settings/google/connect` | JWT + PIN | Connect Google Account |
| DELETE | `/settings/google/disconnect` | JWT + PIN | Disconnect Google Account |
| GET | `/settings/google/storage` | JWT + PIN | Get Drive storage usage |

### 4.16 Help
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/help/manual` | JWT + PIN | Get role-specific manual sections |
| GET | `/help/line-qr` | JWT + PIN | Get LINE QR codes |

---

## 5. Environment & Configuration

### 5.1 `.env.example`
```env
# === Application ===
APP_NAME=studio-management
APP_ENV=development                     # development | staging | production
DEBUG=true
SECRET_KEY=your-secret-key-here        # JWT signing key (min 32 chars)
ALLOWED_ORIGINS=http://localhost:3000  # CORS origins (comma-separated)

# === Database ===
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=studio_management
POSTGRES_USER=studio_user
POSTGRES_PASSWORD=your-db-password

# === Redis ===
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# === JWT ===
JWT_ALGORITHM=HS256
JWT_LOGIN_EXPIRE_DAYS=30               # Login session duration (developer configurable)
JWT_PIN_EXPIRE_HOURS=5                 # PIN session duration (fixed 5h)

# === Rate Limiting ===
RATE_LIMIT_LOGIN_MAX=10                # Max wrong password attempts
RATE_LIMIT_LOGIN_WINDOW_SECONDS=900    # Window: 15 minutes
RATE_LIMIT_OTP_MAX=3                   # Max OTP requests
RATE_LIMIT_OTP_WINDOW_SECONDS=60       # Window: 60 seconds
PIN_LOCKOUT_ATTEMPTS=5                 # Wrong PIN attempts before lockout

# === Email (SMTP) ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourstudio.com
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=Studio Management <noreply@yourstudio.com>

# === Google OAuth ===
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/settings/google/callback

# === Google Drive ===
GOOGLE_DRIVE_STORAGE_WARNING_PERCENT=90  # Warn when Drive > 90% full

# === Celery (Async Tasks) ===
CELERY_BROKER_URL=redis://:your-redis-password@redis:6379/0
CELERY_RESULT_BACKEND=redis://:your-redis-password@redis:6379/1

# === External Booking API ===
EXTERNAL_BOOKING_API_KEY=your-external-api-key  # For customer product integration

# === Encryption ===
ENCRYPTION_KEY=your-32-byte-encryption-key      # For Google token encryption at rest
```

---

## 6. Docker Configuration

### 6.1 `docker-compose.yml`
```yaml
version: "3.9"

services:

  # ─── PostgreSQL Database ───────────────────────────────
  db:
    image: postgres:16-alpine
    container_name: studio-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"          # Expose only for local dev; remove in production
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── Redis (Cache + Rate Limit + Session) ─────────────
  redis:
    image: redis:7-alpine
    container_name: studio-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"          # Expose only for local dev; remove in production
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # ─── FastAPI Application ───────────────────────────────
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: studio-api
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_HOST: db
      REDIS_HOST: redis
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./api:/app                     # Hot reload in dev (removed in prod)
    ports:
      - "8000:8000"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # ─── Celery Worker (Async Tasks) ──────────────────────
  worker:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: studio-worker
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_HOST: db
      REDIS_HOST: redis
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./api:/app
    command: celery -A tasks worker --loglevel=info --concurrency=4

  # ─── Nginx Reverse Proxy ───────────────────────────────
  nginx:
    image: nginx:alpine
    container_name: studio-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro    # SSL certificates
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### 6.2 `docker-compose.dev.yml` (Development Override)
```yaml
version: "3.9"

services:
  api:
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./api:/app
    environment:
      DEBUG: "true"

  worker:
    command: celery -A tasks worker --loglevel=debug --concurrency=2

  db:
    ports:
      - "5432:5432"    # Expose DB port for direct access in dev

  redis:
    ports:
      - "6379:6379"    # Expose Redis port for direct access in dev
```

### 6.3 `api/Dockerfile`
```dockerfile
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies for psycopg2 (PostgreSQL adapter)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run database migrations then start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.4 `api/requirements.txt`
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
alembic==1.13.3
psycopg2-binary==2.9.10
pydantic==2.9.0
pydantic-settings==2.6.0
python-jose[cryptography]==3.3.0   # JWT
passlib[bcrypt]==1.7.4              # Password hashing
python-multipart==0.0.12            # File upload
redis==5.1.1                        # Redis client
celery==5.4.0                       # Async task queue
httpx==0.27.2                       # Async HTTP (for Google API)
google-auth==2.35.0                 # Google OAuth
google-api-python-client==2.150.0  # Google Drive/Sheets
cryptography==43.0.3                # Token encryption at rest
pyotp==2.9.0                        # OTP generation
emails==0.6.0                       # Email sending
pillow==11.0.0                      # Image processing (profile photos)
```

---

## 7. Key Middleware & Dependencies

### 7.1 Authentication Dependency Chain
```
get_current_user()          → Validates JWT, returns user object
  └── require_pin_verified() → Checks PIN session (< 5h), blocks if expired
        └── require_roles(*roles) → Checks user.role is in allowed list
              └── check_feature_toggle(module) → Checks feature is enabled
                    └── check_permission(module, action) → Checks matrix
```

### 7.2 Branch Scope Filter
Every list endpoint automatically filters by branch based on role:
```python
# Applied automatically as dependency
def apply_branch_filter(current_user: User) -> BranchFilter:
    # developer → no filter (see all partners/branches)
    # owner     → filter by partner_id
    # others    → filter by branch_id
```

### 7.3 Rate Limiting (Redis-based)
```
POST /auth/login       → max 10 attempts per IP per 15 min
POST /auth/pin/verify  → max 5 attempts per user (lockout)
POST /auth/pin/forgot  → max 3 requests per user per 60s
```

### 7.4 Activity Log Middleware
All write operations (POST/PUT/DELETE) automatically create activity log entries via middleware, capturing: actor, action, target, before/after changes.

---

## 8. Pipeline Status Update

| Step | Description | Status |
|------|-------------|--------|
| 1-9 | Context, Requirements, FE Design, Test Cases | ✅ Done |
| 10 | BE Design (this document) | ✅ Done |
| 11 | Automation Test Setup | ⬜ Next |
| 12 | Build Web App (FE + BE) | ⬜ Pending |
