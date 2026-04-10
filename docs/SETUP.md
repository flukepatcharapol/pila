# SETUP.md — Studio Management
## Infrastructure Setup Guide (from scratch)
### สำหรับคนที่มีแค่ Python3 ในเครื่อง

---

## สิ่งที่จะติดตั้งในไฟล์นี้

| Tool | ไว้ทำอะไร |
|------|-----------|
| Homebrew | Package manager สำหรับ macOS — ใช้ติดตั้งทุกอย่าง |
| Git | Version control — ติดตาม code changes |
| Node.js + npm | Runtime สำหรับ FE (React) |
| Docker Desktop | รัน PostgreSQL, Redis, Nginx แบบ container |
| pgAdmin 4 | GUI สำหรับดู/จัดการ PostgreSQL database |

---

## ขั้นตอนที่ 1 — ติดตั้ง Homebrew

Homebrew คือ package manager ของ macOS ใช้ติดตั้ง software ต่างๆ ผ่าน terminal ได้สะดวก

```bash
# คำสั่งนี้จะ download และรัน script ติดตั้ง Homebrew อัตโนมัติ
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

หลังติดตั้งเสร็จ ให้รัน 2 คำสั่งนี้ตาม instruction ที่ terminal แสดง (เพื่อเพิ่ม Homebrew ใน PATH):

```bash
# เพิ่ม Homebrew ใน shell profile (ทำครั้งเดียว)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile

# โหลด config ใหม่ทันทีโดยไม่ต้องปิด terminal
eval "$(/opt/homebrew/bin/brew shellenv)"
```

ตรวจสอบว่าติดตั้งสำเร็จ:

```bash
# ควรแสดงเวอร์ชั่น เช่น "Homebrew 4.x.x"
brew --version
```

---

## ขั้นตอนที่ 2 — ติดตั้ง Git

Git ใช้สำหรับ version control — ติดตาม, บันทึก, และแชร์ code กับทีม

```bash
# ติดตั้ง Git ผ่าน Homebrew
brew install git
```

ตรวจสอบ:

```bash
# ควรแสดงเวอร์ชั่น เช่น "git version 2.x.x"
git --version
```

ตั้งค่า identity ของคุณใน Git (ใช้ครั้งเดียว):

```bash
# ชื่อนี้จะปรากฏใน git commit ทุกอัน
git config --global user.name "Your Name"

# email นี้จะเชื่อมกับ commit ของคุณ
git config --global user.email "your@email.com"
```

---

## ขั้นตอนที่ 3 — ติดตั้ง Node.js + npm

Node.js คือ runtime ที่ FE (React) ต้องใช้ในการ build และ run
npm คือ package manager ของ Node.js ใช้ติดตั้ง library ต่างๆ

```bash
# ติดตั้ง Node.js (npm จะติดมาด้วยอัตโนมัติ)
brew install node
```

ตรวจสอบ:

```bash
# ควรแสดง Node.js version เช่น "v22.x.x"
node --version

# ควรแสดง npm version เช่น "10.x.x"
npm --version
```

---

## ขั้นตอนที่ 4 — ติดตั้ง Docker Desktop

Docker คือ platform ที่ใช้รัน services (PostgreSQL, Redis, Nginx) แบบ container
แทนที่จะติดตั้งลงเครื่องตรงๆ Docker จะสร้าง environment แยกต่างหาก ไม่กระทบเครื่อง

```bash
# ติดตั้ง Docker Desktop ผ่าน Homebrew
brew install --cask docker
```

หลังติดตั้ง:
1. เปิด **Docker Desktop** จาก Applications
2. รอให้ icon ใน menu bar แสดงว่า Docker กำลัง running (icon จะหยุดกระพริบ)
3. ตรวจสอบ:

```bash
# ควรแสดง Docker version เช่น "Docker version 27.x.x"
docker --version

# ควรแสดง Docker Compose version เช่น "Docker Compose version v2.x.x"
docker compose version
```

---

## ขั้นตอนที่ 5 — ติดตั้ง pgAdmin 4 (Optional แต่แนะนำ)

pgAdmin คือ GUI tool สำหรับดูและจัดการ PostgreSQL database
มีประโยชน์มากตอน debug หรือตรวจสอบข้อมูลใน DB

```bash
# ติดตั้ง pgAdmin 4
brew install --cask pgadmin4
```

---

## ขั้นตอนที่ 6 — Clone Repositories

```bash
# สร้าง folder สำหรับ project (ชื่อได้ตามต้องการ)
mkdir studio-management && cd studio-management

# Clone BE repository
git clone <BE_REPO_URL> backend

# Clone FE repository
git clone <FE_REPO_URL> frontend
```

โครงสร้าง folder หลังจาก clone:

```
studio-management/
├── backend/        ← FastAPI + Python
└── frontend/       ← React + TypeScript
```

---

## ขั้นตอนที่ 7 — สร้างไฟล์ Environment Variables

ทั้ง BE และ FE ต้องการไฟล์ `.env` สำหรับ config ต่างๆ
(ไฟล์ `.env` จะไม่ถูก commit ขึ้น Git เพราะเก็บ secret)

```bash
# สร้าง .env สำหรับ BE จาก template
cp backend/.env.example backend/.env

# เปิดแก้ไขค่าใน .env ตามความเหมาะสม
nano backend/.env
# หรือใช้ VS Code: code backend/.env
```

ค่าที่ต้องแก้ขั้นต่ำ:

```env
SECRET_KEY=           # เปลี่ยนเป็น random string อย่างน้อย 32 ตัวอักษร
POSTGRES_PASSWORD=    # ตั้ง password สำหรับ database
REDIS_PASSWORD=       # ตั้ง password สำหรับ Redis
```

---

## ขั้นตอนที่ 8 — รัน Infrastructure ด้วย Docker

```bash
# เข้าไปใน folder backend ที่มี docker-compose.yml
cd backend

# รัน services ทั้งหมด (PostgreSQL, Redis, Nginx) แบบ background
# flag -d = detached mode (รันใน background ไม่ block terminal)
docker compose up -d db redis

# ตรวจสอบว่า services รันอยู่
# STATUS ควรเป็น "healthy" หรือ "running"
docker compose ps
```

---

## ขั้นตอนที่ 9 — รัน Database Migrations

Migration คือการสร้าง tables ใน database ตาม schema ที่ design ไว้

```bash
# รัน migration เพื่อสร้าง tables ทั้งหมดใน PostgreSQL
docker compose run --rm api alembic upgrade head
```

---

## ขั้นตอนที่ 10 — ตรวจสอบ pgAdmin

1. เปิด pgAdmin 4
2. Add Server ใหม่:
   - **Host:** `localhost`
   - **Port:** `5432`
   - **Database:** `studio_management`
   - **Username:** ค่าจาก `POSTGRES_USER` ใน `.env`
   - **Password:** ค่าจาก `POSTGRES_PASSWORD` ใน `.env`
3. ตรวจสอบว่า tables ถูกสร้างครบ

---

## Quick Commands Reference

```bash
# รัน services ทั้งหมด
docker compose up -d

# หยุด services ทั้งหมด
docker compose down

# ดู logs ของ service ใดๆ
docker compose logs -f api        # ดู BE logs
docker compose logs -f db         # ดู DB logs
docker compose logs -f redis      # ดู Redis logs

# รัน migration ใหม่
docker compose run --rm api alembic upgrade head

# เข้าไปใน container เพื่อ debug
docker compose exec api bash
docker compose exec db psql -U studio_user -d studio_management
```
