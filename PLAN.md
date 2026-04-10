# Pila Monorepo — Scaffold Plan

> สถานะ: **รอ review** ก่อนเริ่มสร้างจริง
> อิงเอกสารต้นทางทั้งหมดที่ `C:\Users\UsEr\Documents\co_work\Pila\docs\Document\`

---

## 1. Context

ต้องสร้าง monorepo `Pila_code` ใหม่จาก scratch โดย:

- มีเอกสารแผน (design, test plan, coding standards) และไฟล์ test/config **พร้อมใช้** อยู่แล้วที่ `Pila\docs\Document\`
- ต้องวาง/ปรับไฟล์พวกนั้นให้เข้าโครงสร้างที่ผู้ใช้กำหนด (nested tests)
- Scaffold ไฟล์โครง BE/FE ที่ยังไม่มี (FastAPI app, React+TS+Vite app, Docker, infra)

### Decisions ที่ confirmed แล้ว

| ประเด็น | ตัดสินใจ |
|---|---|
| โครง tests | **Nested** — `backend/tests/be`, `frontend/tests/fe`, `tests/integration` |
| FE language | **TypeScript** (ตามเอกสาร) |
| FE unit test (Vitest) | **ไม่ใช้** — FE tests เป็น Playwright-Python ผ่าน pytest ทั้งหมด |
| BE stack | Python 3.12 + uv + FastAPI + SQLAlchemy + Alembic + Celery |
| Infra | docker-compose: backend, frontend, postgres, redis (+ celery worker, nginx ตามเอกสาร) |
| Styling | Tailwind + CSS variables (globals.css) |

---

## 2. Key conflict: pytest paths

เอกสารต้นฉบับออกแบบโดยให้ **tests ทั้งหมดอยู่ที่ root `tests/`** แต่คุณต้องการ **nested** ผมจะแก้โดย:

1. **`pytest.ini` ที่ root** — เปลี่ยน `testpaths = tests` เป็น:
   ```ini
   testpaths = backend/tests frontend/tests tests/integration
   ```
2. **Root `conftest.py`** ที่ root ของ monorepo (ไม่ใช่ใน `tests/`) — มาจาก `conftest_root.py` ทำหน้าที่โหลด `.env.test` + session fixtures (base_url, fe_base_url, test_credentials, hook สำหรับ fallback locator)
3. **`backend/tests/be/conftest.py`** — มาจาก `conftest_be.py` (DB, async client, token factories)
4. **`frontend/tests/fe/conftest.py`** — มาจาก `conftest_fe.py` (browser context, logged_in_page_factory)
5. **`tests/integration/conftest.py`** — สร้างใหม่บางๆ ที่ inherit จาก root (เนื่องจาก root conftest ให้ fixtures ร่วมอยู่แล้ว)
6. **`playwright.config.ts`** วางที่ `frontend/playwright.config.ts` — ในไฟล์มี `testDir: "./tests/fe"` ซึ่ง resolve เป็น `frontend/tests/fe/` ตรงกับ nested structure อยู่แล้ว ✅ **ไม่ต้องแก้**
7. Running: `cd Pila_code && pytest` จะเก็บทั้ง 3 layer; หรือเจาะจง `pytest backend/tests/be`, `pytest frontend/tests/fe`, `pytest tests/integration`

> **หมายเหตุ**: pytest discover conftest.py โดยอัตโนมัติจาก rootdir ลงมา ดังนั้น root conftest.py จะ apply กับทุก test ใต้ `backend/tests`, `frontend/tests`, `tests/` ได้ทันที

---

## 3. Target directory structure

```
Pila_code/
├── pytest.ini                          ← จาก docs/pytest.ini (แก้ testpaths)
├── .env.test                           ← จาก docs/.env.test
├── conftest.py                         ← จาก docs/conftest_root.py (root-level)
├── docker-compose.yml                  ← ใหม่
├── docker-compose.dev.yml              ← ใหม่ (ตาม BE_README.md)
├── .gitignore                          ← ใหม่
├── README.md                           ← ใหม่ (monorepo overview)
│
├── docs/                               ← ทุกไฟล์ .md จาก docs/Document/ ย้ายมาที่นี่
│   ├── 00_coding_standards.md
│   ├── 01_fe_requirements_analysis.md
│   ├── 02_fe_testcases_V_0_2.md
│   ├── 03_be_testcases_V_0_2.md
│   ├── 04_integration_testcases_V_0_2.md
│   ├── 05_be_design.md
│   ├── 06_automation_test_plan.md
│   ├── 07_be_diagrams.md
│   ├── requirements.md
│   └── SETUP.md
│
├── backend/
│   ├── README.md                       ← จาก docs/BE_README.md
│   ├── pyproject.toml                  ← scaffold ใหม่ (uv + FastAPI + Alembic + Celery)
│   ├── .python-version                 ← "3.12"
│   ├── .env.example                    ← scaffold ใหม่
│   ├── Dockerfile                      ← scaffold ใหม่
│   ├── api/                            ← main FastAPI app (ตาม 05_be_design.md)
│   │   ├── __init__.py
│   │   ├── main.py                     ← FastAPI app + /health
│   │   ├── config.py                   ← pydantic BaseSettings
│   │   ├── database.py                 ← SQLAlchemy engine/session
│   │   ├── models/__init__.py          ← (stub) Partner, Branch, User, Customer, ...
│   │   ├── schemas/__init__.py         ← (stub) pydantic models
│   │   ├── routers/__init__.py         ← (stub) auth, customer, order, ...
│   │   ├── services/__init__.py        ← (stub) business logic
│   │   ├── dependencies/__init__.py    ← (stub) auth deps, DB session
│   │   ├── middleware/__init__.py      ← (stub)
│   │   ├── tasks/__init__.py           ← (stub) Celery tasks
│   │   ├── utils/__init__.py           ← (stub)
│   │   └── migrations/                 ← Alembic (init ทีหลัง)
│   │       └── .gitkeep
│   ├── worker/                         ← (stub) Celery worker
│   │   └── __init__.py
│   └── tests/
│       └── be/
│           ├── __init__.py
│           ├── conftest.py             ← จาก docs/conftest_be.py
│           ├── helpers/
│           │   ├── __init__.py
│           │   └── common_api.py       ← จาก docs/common_api.py
│           ├── test_auth_api.py        ← จาก docs/test_auth_api.py
│           └── test_customer_api.py    ← จาก docs/test_customer_api.py
│
├── frontend/
│   ├── README.md                       ← จาก docs/FE_README.md
│   ├── package.json                    ← scaffold ใหม่ (React+TS+Vite+Tailwind)
│   ├── tsconfig.json                   ← scaffold ใหม่
│   ├── tsconfig.node.json              ← scaffold ใหม่
│   ├── vite.config.ts                  ← scaffold ใหม่
│   ├── tailwind.config.ts              ← จาก docs/tailwind.config.ts
│   ├── postcss.config.js               ← scaffold ใหม่ (Tailwind plugin)
│   ├── playwright.config.ts            ← จาก docs/playwright.config.ts (ไม่แก้)
│   ├── index.html                      ← scaffold ใหม่
│   ├── Dockerfile                      ← scaffold ใหม่
│   ├── .env.example                    ← VITE_API_URL, VITE_APP_NAME
│   ├── .gitignore                      ← scaffold ใหม่
│   ├── src/
│   │   ├── main.tsx                    ← scaffold ใหม่
│   │   ├── App.tsx                     ← scaffold ใหม่
│   │   ├── vite-env.d.ts               ← scaffold ใหม่
│   │   ├── pages/                      ← (stub directory)
│   │   ├── components/                 ← (stub)
│   │   ├── hooks/                      ← (stub)
│   │   ├── stores/                     ← (stub)
│   │   ├── api/                        ← (stub)
│   │   ├── types/                      ← (stub)
│   │   ├── utils/                      ← (stub)
│   │   └── styles/
│   │       └── globals.css             ← จาก docs/globals.css
│   └── tests/
│       └── fe/
│           ├── __init__.py
│           ├── conftest.py             ← จาก docs/conftest_fe.py
│           ├── helpers/
│           │   ├── __init__.py
│           │   └── common_web.py       ← จาก docs/common_web.py
│           ├── test_auth.py            ← จาก docs/test_auth.py
│           └── test_customer.py        ← จาก docs/test_customer.py
│
└── tests/
    └── integration/
        ├── __init__.py
        ├── conftest.py                 ← scaffold ใหม่ (บางๆ, ใช้ fixtures จาก root)
        └── test_example_flow.py        ← stub (ยังไม่มีในเอกสาร)
```

---

## 4. File-by-file mapping (จาก docs/Document/ → target)

| ต้นทาง | ปลายทาง | หมายเหตุ |
|---|---|---|
| `pytest.ini` | `Pila_code/pytest.ini` | **แก้** `testpaths` เป็น `backend/tests frontend/tests tests/integration` |
| `.env.test` | `Pila_code/.env.test` | copy ตรงๆ |
| `conftest_root.py` | `Pila_code/conftest.py` | **ย้ายไป root ของ monorepo** (ไม่ใช่ใน `tests/`) เพราะ pytest rootdir = monorepo root |
| `conftest_be.py` | `Pila_code/backend/tests/be/conftest.py` | copy; imports จาก `api.*` ต้องตรงกับ BE layout |
| `conftest_fe.py` | `Pila_code/frontend/tests/fe/conftest.py` | copy ตรงๆ |
| `common_api.py` | `Pila_code/backend/tests/be/helpers/common_api.py` | copy ตรงๆ |
| `common_web.py` | `Pila_code/frontend/tests/fe/helpers/common_web.py` | copy ตรงๆ |
| `test_auth_api.py` | `Pila_code/backend/tests/be/test_auth_api.py` | copy; อาจต้องแก้ import path ของ helpers |
| `test_customer_api.py` | `Pila_code/backend/tests/be/test_customer_api.py` | copy; อาจต้องแก้ import path |
| `test_auth.py` | `Pila_code/frontend/tests/fe/test_auth.py` | copy; อาจต้องแก้ import path |
| `test_customer.py` | `Pila_code/frontend/tests/fe/test_customer.py` | copy; อาจต้องแก้ import path |
| `playwright.config.ts` | `Pila_code/frontend/playwright.config.ts` | copy ตรงๆ (testDir `./tests/fe` ถูกแล้ว) |
| `tailwind.config.ts` | `Pila_code/frontend/tailwind.config.ts` | copy ตรงๆ |
| `globals.css` | `Pila_code/frontend/src/styles/globals.css` | copy ตรงๆ |
| `BE_README.md` | `Pila_code/backend/README.md` | copy (rename) |
| `FE_README.md` | `Pila_code/frontend/README.md` | copy (rename) |
| `SETUP.md` | `Pila_code/docs/SETUP.md` | copy |
| `00_coding_standards.md` ... `07_be_diagrams.md` | `Pila_code/docs/<same name>` | copy |
| `requirements.md` | `Pila_code/docs/requirements.md` | copy |

### ไฟล์ที่ต้องสร้างใหม่ (ไม่มีในเอกสาร)

**Backend:**
- `backend/pyproject.toml` — uv project; deps: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `redis`, `celery`, `pydantic-settings`, `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`; dev deps: `pytest`, `pytest-asyncio`, `httpx`, `pytest-playwright`, `allure-pytest`, `python-dotenv`
- `backend/.python-version` — `3.12`
- `backend/.env.example`
- `backend/Dockerfile` — python:3.12-slim + uv
- `backend/api/main.py` — minimal FastAPI + /health
- `backend/api/config.py` — Settings (pydantic)
- `backend/api/database.py` — engine + get_db dependency
- stubs: `api/__init__.py`, `api/{models,schemas,routers,services,dependencies,middleware,tasks,utils}/__init__.py`, `api/migrations/.gitkeep`, `worker/__init__.py`

**Frontend:**
- `frontend/package.json` — deps: `react`, `react-dom`, `react-router-dom`; devDeps: `@types/react`, `@types/react-dom`, `typescript`, `vite`, `@vitejs/plugin-react`, `tailwindcss`, `postcss`, `autoprefixer`, `@playwright/test`
- `frontend/tsconfig.json`, `frontend/tsconfig.node.json`
- `frontend/vite.config.ts`
- `frontend/postcss.config.js`
- `frontend/index.html`
- `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/vite-env.d.ts`
- `frontend/Dockerfile` — node:20-alpine
- `frontend/.env.example`
- `frontend/.gitignore`

**Root:**
- `docker-compose.yml` — backend, frontend, postgres (16), redis (7), worker (Celery); healthchecks; volumes
- `docker-compose.dev.yml` — override for dev
- `.gitignore` — Python (__pycache__, .venv, .pytest_cache, allure-results), Node (node_modules, dist), editors, OS
- `README.md` — monorepo overview, setup, test commands, links to docs/
- `tests/integration/conftest.py` — minimal (reuse root fixtures)
- `tests/integration/test_example_flow.py` — placeholder

---

## 5. ไฟล์ที่ต้องลบ/ทับ (ที่ผม scaffold ไปก่อนหน้านี้)

ช่วงก่อน user ส่งเอกสารมา ผม scaffold ไปแล้วบางส่วน ต้อง **รื้อทิ้ง**:

- ❌ `backend/app/` → เปลี่ยนเป็น `backend/api/`
- ❌ `backend/pyproject.toml` ปัจจุบัน → rewrite (เพิ่ม celery, alembic, allure-pytest, pytest-playwright ฯลฯ)
- ❌ `backend/tests/be/conftest.py`, `test_health.py` → ทับด้วยของจริงจากเอกสาร (แต่ test_health อาจเก็บไว้เป็น smoke)
- ❌ `frontend/package.json` → rewrite เป็น TypeScript + Tailwind (ลบ Vitest)
- ❌ `frontend/vite.config.js` → เปลี่ยนเป็น `vite.config.ts` (ลบ vitest block)
- ❌ `frontend/src/main.jsx`, `App.jsx` → เปลี่ยนเป็น `.tsx`
- ❌ `frontend/tests/fe/*` (Vitest ของเดิม) → ทับด้วยของจริง (Playwright-Python)

---

## 6. Import path considerations

ไฟล์ test จากเอกสารสมมติว่า test อยู่ที่ `tests/be/` และ helpers ที่ `tests/be/helpers/`. เมื่อย้ายมา nested:

- `backend/tests/be/test_auth_api.py` จะ `from helpers.common_api import ...` ได้ถ้า `backend/tests/be/` เป็น rootdir หรือถ้าเราใส่ `__init__.py` และใช้ relative import `from .helpers.common_api import ...`
- **ทางเลือก**: ใช้ `from tests.be.helpers.common_api import ...` โดยใส่ `pythonpath = . backend frontend` ใน pytest.ini
- **แนะนำ**: ใส่ `pythonpath = backend/tests backend/tests/be frontend/tests frontend/tests/fe` ใน pytest.ini เพื่อให้ `from helpers.common_api import ...` ทำงานได้โดยตรง (minimal diff จากของเดิม)

จะ **ตรวจสอบไฟล์ test จริง** ก่อน apply เพื่อดูรูปแบบ import ที่ใช้จริงและปรับให้เหมาะสม

---

## 7. Verification plan

หลัง scaffold เสร็จ:

1. **BE unit-ish tests** — `cd Pila_code && pytest backend/tests/be -v`
   คาด: tests รันได้ (อาจ fail ถ้า seed data/DB ยังไม่พร้อม แต่ collection ต้องสำเร็จ)
2. **FE tests** — `cd Pila_code && pytest frontend/tests/fe -v`
   คาด: collection สำเร็จ, Playwright browser พร้อม (ต้องรัน `playwright install` ก่อน)
3. **Config sanity** — `cd Pila_code && pytest --collect-only`
   คาด: เก็บ tests ครบ 3 layer ไม่มี ImportError
4. **Stack up** — `docker compose up --build -d` → `curl localhost:8000/health`, `curl -I localhost:5173`
5. **Integration** (optional, ถ้ามี placeholder) — `pytest tests/integration -v`

---

## 8. Out of scope (รอบนี้ไม่ทำ)

- Alembic migrations จริง (แค่ตั้ง folder + init config)
- Business models (Partner, Branch, User, Customer, ...) — แค่ stub `__init__.py`
- Actual FastAPI routers — แค่ /health
- Celery tasks จริง — แค่ `worker/__init__.py`
- Frontend pages/components จริง — แค่ App.tsx "Hello"
- CI workflows
- ทำให้ tests ทั้งหมด **pass** — แค่ทำให้ collection สำเร็จและรันได้จนถึงจุดที่ seed data หายไป (tests fail เพราะ env ไม่ครบ ≠ scaffold พัง)

---

## 9. ลำดับการทำงานหลัง approve

1. รื้อไฟล์ที่ผม scaffold ผิดไว้ก่อน (`backend/app/*`, `frontend/*.js*`)
2. สร้างโครง BE ใหม่ (`backend/api/*`, pyproject.toml, Dockerfile)
3. สร้างโครง FE ใหม่ (`frontend/src/*.tsx`, vite.config.ts, tsconfig, Tailwind, postcss)
4. Copy ไฟล์ docs, pytest.ini, .env.test, conftest_*, test_*, helpers, playwright.config.ts, tailwind.config.ts, globals.css (พร้อมปรับ path ตามข้อ 6)
5. สร้าง `docker-compose.yml`, root `.gitignore`, root `README.md`, root `conftest.py`
6. รัน verification ข้อ 7

---

## 10. คำถามที่ยังเปิดอยู่

1. **Celery worker + nginx**: เอกสาร BE_README กล่าวถึง ต้องการให้ scaffold โครงด้วยไหม (แค่ folder + stub) หรือข้ามไปรอบหน้า?
2. **Alembic init**: ต้องรัน `alembic init` จริงไหม หรือแค่เตรียม folder?
3. **Integration tests**: ในเอกสารไม่มีไฟล์ test_integration ต้นฉบับ ให้สร้าง placeholder ว่างๆ หรือรอ user?
4. **Playwright browsers**: ต้องรัน `playwright install` ให้เลยไหม (download ~300MB) หรือใส่ใน README ให้ user รันเอง?
5. **Imports ใน test files**: ขอ review **test_auth_api.py, test_customer_api.py, test_auth.py, test_customer.py** ก่อนจริง เพื่อดูว่า import helpers ยังไง — ถ้าเป็น `from helpers.common_api import ...` ต้องตั้ง `pythonpath` ใน pytest.ini; ถ้าเป็น `from tests.be.helpers.common_api import ...` ต้องตั้งคนละแบบ
