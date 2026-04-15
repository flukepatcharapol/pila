# Studio Management — Backend
## FastAPI + PostgreSQL + Python 3.12

---

## สิ่งที่ต้องมีก่อน

ติดตั้งตาม `SETUP.md` ก่อน จนครบทุกขั้นตอน แล้วค่อยมาทำต่อที่นี่

| Requirement | Version | ตรวจสอบด้วย |
|-------------|---------|------------|
| Python | 3.12+ | `python3 --version` |
| Docker Desktop | 27+ | `docker --version` |
| Git | 2+ | `git --version` |

---

## โครงสร้างโปรเจกต์

```
backend/
├── api/                        # FastAPI application หลัก
│   ├── main.py                 # Entry point — สร้าง FastAPI app และ register routers
│   ├── config.py               # อ่าน environment variables ด้วย pydantic BaseSettings
│   ├── database.py             # สร้าง SQLAlchemy engine และ session factory
│   │
│   ├── models/                 # SQLAlchemy ORM models (แต่ละไฟล์ = แต่ละ DB table)
│   ├── schemas/                # Pydantic schemas (validate request/response data)
│   ├── routers/                # API route handlers (แต่ละไฟล์ = แต่ละ module)
│   ├── services/               # Business logic (แยก logic ออกจาก router)
│   ├── dependencies/           # FastAPI dependency injection (auth, permission, scope)
│   ├── middleware/             # Request/response middleware (rate limit, activity log)
│   ├── tasks/                  # Celery async tasks (email, Google Drive)
│   ├── utils/                  # Utility functions (security, pagination, validators)
│   └── migrations/             # Alembic database migration files
│
├── worker/                     # Celery worker configuration
├── nginx/                      # Nginx config
├── docker-compose.yml          # Production services
├── docker-compose.dev.yml      # Development overrides
├── .env.example                # Template สำหรับ environment variables
└── README.md                   # ไฟล์นี้
```

---

## ขั้นตอนที่ 1 — Clone และเตรียม Project

```bash
# Clone repository
git clone <BE_REPO_URL> backend
cd backend
```

---

## ขั้นตอนที่ 2 — สร้าง Virtual Environment

Virtual environment คือ Python environment แยกสำหรับโปรเจกต์นี้โดยเฉพาะ
ป้องกัน library ของโปรเจกต์นี้ไปชนกับโปรเจกต์อื่นในเครื่อง

```bash
# สร้าง virtual environment ชื่อ "venv" ใน folder ปัจจุบัน
python3 -m venv venv

# เปิดใช้งาน virtual environment
# (ต้องรันทุกครั้งที่เปิด terminal ใหม่)
source venv/bin/activate

# ตรวจสอบว่า activate สำเร็จ
# terminal ควรแสดง (venv) นำหน้า prompt เช่น "(venv) user@mac backend %"
which python
```

---

## ขั้นตอนที่ 3 — ติดตั้ง Dependencies

```bash
# ติดตั้ง Python packages ทั้งหมดที่โปรเจกต์ต้องการ
# flag -r = อ่านจากไฟล์ requirements.txt
pip install -r api/requirements.txt

# ตรวจสอบว่าติดตั้งสำเร็จ (ควรเห็น fastapi, sqlalchemy, etc.)
pip list
```

---

## ขั้นตอนที่ 4 — ตั้งค่า Environment Variables

```bash
# คัดลอก template มาสร้างไฟล์ .env จริง
cp .env.example .env

# เปิดแก้ไข .env
nano .env
```

ค่าสำคัญที่ต้องแก้:

```env
# ===== ต้องแก้ก่อน run =====

# Random string อย่างน้อย 32 ตัวอักษร — ใช้เซ็น JWT tokens
# generate ได้ด้วย: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-here

# Password สำหรับ PostgreSQL database
POSTGRES_PASSWORD=your-db-password

# Password สำหรับ Redis
REDIS_PASSWORD=your-redis-password

# ===== แก้ถ้ามี =====

# SMTP สำหรับส่ง email (OTP, receipt)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password    # Gmail App Password (ไม่ใช่ password login)

# Google OAuth (สำหรับ Google Drive integration)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

---

## ขั้นตอนที่ 5 — รัน Database และ Redis

```bash
# รัน PostgreSQL และ Redis ผ่าน Docker
# flag -d = รันใน background
docker compose up -d db redis

# รอสักครู่แล้วตรวจสอบว่า services ขึ้นมา
# STATUS ควรเป็น "healthy"
docker compose ps
```

---

## ขั้นตอนที่ 6 — รัน Database Migrations

Migration คือการสร้าง/อัปเดต tables ใน database ตาม schema ที่ define ไว้ใน models/

```bash
# เข้าไปใน folder api/
cd api

# รัน migration เพื่อสร้าง tables ทั้งหมด
# "head" หมายถึง apply migration ล่าสุดทั้งหมด
alembic upgrade head

# ตรวจสอบ migration status
# ควรแสดง revision ปัจจุบัน
alembic current
```

---

## ขั้นตอนที่ 7 — รัน Development Server

```bash
# กลับมาที่ root folder ของ backend
cd ..

# รัน FastAPI server แบบ development (hot reload)
# --reload = server restart อัตโนมัติทุกครั้งที่แก้ไข code
# --host 0.0.0.0 = รับ connection จากทุก IP (ไม่ใช่แค่ localhost)
# --port 8000 = port ที่ใช้
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

เปิด browser ไปที่:
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

---

## ขั้นตอนที่ 8 — รัน Celery Worker (Async Tasks)

Celery worker ใช้สำหรับงานที่ทำใน background เช่น ส่ง email, generate Google Sheet

```bash
# เปิด terminal ใหม่ แล้ว activate venv ก่อน
source venv/bin/activate

# รัน Celery worker
# -A tasks = ชี้ไปที่ celery app ใน tasks/
# worker = คำสั่งรัน worker
# --loglevel=info = แสดง log ระดับ info ขึ้นไป
celery -A api.tasks worker --loglevel=info
```

---

## ขั้นตอนที่ 9 — รัน ด้วย Docker (แบบเต็ม)

ถ้าต้องการรันทุกอย่างผ่าน Docker (เหมือน production):

```bash
# รัน services ทั้งหมด: db, redis, api, worker, nginx
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# ดู logs แบบ real-time
docker compose logs -f api

# หยุดทุกอย่าง
docker compose down
```

---

## การสร้าง Migration ใหม่

เมื่อแก้ไข model (เพิ่ม/ลบ column หรือ table) ต้องสร้าง migration:

```bash
cd api

# สร้าง migration file อัตโนมัติจาก model changes
# -m = ชื่อ migration (อธิบายว่าเปลี่ยนอะไร)
alembic revision --autogenerate -m "add caretaker_id to bookings"

# Apply migration ที่สร้างใหม่
alembic upgrade head

# ถ้าต้องการ rollback migration ล่าสุด
alembic downgrade -1
```

---

## การรัน Tests

```bash
# รัน BE test cases ทั้งหมด (rollback ทุก test — ไม่มีข้อมูลเหลือ)
uv run pytest tests/be/ -m "be and not isolated_last" -v

# รัน test เฉพาะ module
uv run pytest tests/be/test_auth_api.py -v

# รัน test พร้อมดู coverage
uv run pytest tests/be/ -v --cov=api --cov-report=html

# รัน พร้อม Allure report
uv run pytest tests/be/ -m "be and not isolated_last" -v --alluredir=allure-results
```

### รัน tests แบบ keep-db (ข้อมูลยังอยู่ใน `pila_test` หลังจบ)

ใช้เมื่อต้องการตรวจสอบ DB state หลัง test เช่น ดูว่าข้อมูลถูก insert ถูกต้องไหม

```bash
# ขั้นตอนที่ 1: รัน tests หลัก (commit แทน rollback)
uv run pytest tests/be/ -m "be and not isolated_last" -v --keep-db

# ขั้นตอนที่ 2: รัน Medium Risk tests แยกหลังสุด
uv run pytest tests/be/ -m "be and isolated_last" -v --keep-db

# ตรวจสอบข้อมูลใน DB
docker compose exec db psql -U pila_user -d pila_test
```

> **หมายเหตุ**: `--keep-db` ใช้สำหรับ debug เท่านั้น อย่าใช้ใน CI/CD pipeline
> ดูรายละเอียดเพิ่มเติมที่ `docs/06_automation_test_plan.md` หัวข้อ 2.6

---

## Quick Commands Reference

```bash
# Activate virtual environment (ทำทุกครั้งที่เปิด terminal ใหม่)
source venv/bin/activate

# รัน development server
uvicorn api.main:app --reload --port 8000

# รัน database
docker compose up -d db redis

# ดู DB logs
docker compose logs -f db

# เข้าไปใน PostgreSQL โดยตรง
docker compose exec db psql -U studio_user -d studio_management

# เข้าไปใน Redis โดยตรง
docker compose exec redis redis-cli -a your-redis-password

# รัน tests
pytest tests/be/ -v

# Format code (ถ้าติดตั้ง black)
black api/

# Check types (ถ้าติดตั้ง mypy)
mypy api/
```

---

## Troubleshooting

**Port 8000 ถูกใช้อยู่แล้ว:**
```bash
# ดูว่า process ไหนใช้ port 8000
lsof -i :8000

# Kill process นั้น (แทน PID ด้วยเลขที่เห็น)
kill -9 <PID>
```

**Database connection refused:**
```bash
# ตรวจสอบว่า Docker container รันอยู่
docker compose ps

# ถ้า container ไม่ขึ้น ดู logs
docker compose logs db
```

**Migration error:**
```bash
# ดู migration history
alembic history

# Reset migration (ระวัง: จะลบข้อมูลทั้งหมด)
alembic downgrade base
alembic upgrade head
```
