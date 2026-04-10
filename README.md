# Pila — Studio Management System

## โครงสร้าง Monorepo

```
Pila_code/
├── backend/          ← FastAPI + Python 3.12 + uv
│   └── tests/be/     ← BE API tests (pytest + httpx + Allure)
├── frontend/         ← React + TypeScript + Vite + Tailwind
│   └── tests/fe/     ← FE browser tests (Playwright-Python + pytest)
├── tests/integration/← End-to-end tests (ต้องการทั้ง BE + FE พร้อมกัน)
└── docs/             ← เอกสาร design, test cases, requirements
```

## Setup

### Prerequisites

- Python 3.12+
- uv (`pip install uv` หรือ `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js 20+
- Docker + Docker Compose

### 1. Backend

```bash
cd backend
uv sync
cp .env.example .env   # แล้วแก้ไข
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # แล้วแก้ไข
```

### 3. Playwright browsers

```bash
cd frontend
npx playwright install chromium
# หรือติดตั้งทุก browser:
npx playwright install
```

### 4. Docker (stack ทั้งหมด)

```bash
docker compose up --build -d
```

## Running Tests

### BE tests เท่านั้น

```bash
pytest backend/tests/be -v
# หรือ
pytest -m be
```

### FE tests เท่านั้น

```bash
pytest frontend/tests/fe -v
# หรือ
pytest -m fe
```

### Integration tests

```bash
pytest tests/integration -v
# หรือ
pytest -m integration
```

### รันทั้งหมด

```bash
pytest
```

### รันพร้อม Allure report

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## Services

| Service  | URL                    |
|----------|------------------------|
| Backend  | http://localhost:8000  |
| Frontend | http://localhost:5173  |
| Postgres | localhost:5432         |
| Redis    | localhost:6379         |

## Docs

ดู `docs/` สำหรับ:
- `SETUP.md` — setup step-by-step
- `requirements.md` — system requirements + roles + design tokens
- `05_be_design.md` — backend design
- `06_automation_test_plan.md` — test plan ทั้งหมด
- `00_coding_standards.md` — coding standards
