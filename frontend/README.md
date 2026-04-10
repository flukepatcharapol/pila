# Studio Management — Frontend
## React + TypeScript + Vite

---

## สิ่งที่ต้องมีก่อน

ติดตั้งตาม `SETUP.md` ก่อน จนครบทุกขั้นตอน แล้วค่อยมาทำต่อที่นี่

| Requirement | Version | ตรวจสอบด้วย |
|-------------|---------|------------|
| Node.js | 22+ | `node --version` |
| npm | 10+ | `npm --version` |
| Git | 2+ | `git --version` |

---

## โครงสร้างโปรเจกต์

```
frontend/
├── public/                     # Static files (favicon, images ที่ไม่ผ่าน build)
├── src/
│   ├── main.tsx                # Entry point — mount React app เข้า DOM
│   ├── App.tsx                 # Root component — setup Router และ global providers
│   │
│   ├── pages/                  # หน้าต่างๆ ของแอพ (1 folder = 1 route)
│   │   ├── auth/               # Login, PIN, Forgot PIN
│   │   ├── dashboard/          # Dashboard (role-based)
│   │   ├── customers/          # Customer list, form, detail
│   │   ├── orders/             # Order list, form, detail
│   │   ├── sessions/           # Session deduct, log, trainer report
│   │   ├── trainers/           # Trainer list, form
│   │   ├── caretakers/         # Caretaker list, form
│   │   ├── packages/           # Package list, form
│   │   ├── bookings/           # Timetable, booking table
│   │   ├── users/              # User management
│   │   ├── permissions/        # Permission matrix
│   │   ├── branches/           # Branch config
│   │   ├── activity-log/       # Activity log
│   │   ├── signature-print/    # Signature print + Google Drive
│   │   ├── settings/           # Settings page
│   │   └── help/               # Help page
│   │
│   ├── components/             # Reusable UI components
│   │   ├── layout/             # Sidebar, Header, PageWrapper
│   │   ├── ui/                 # Base components (Button, Input, Badge, Toast)
│   │   ├── tables/             # DataTable with pagination, sort, search
│   │   ├── forms/              # Form components (ChipSelector, DatePicker, etc.)
│   │   └── modals/             # Modal, Drawer, ConfirmDialog
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts          # Auth state, login, logout
│   │   ├── usePermission.ts    # Check permission matrix
│   │   └── useBranch.ts        # Current branch context
│   │
│   ├── stores/                 # State management (Zustand หรือ Context)
│   │   ├── authStore.ts        # User session, JWT token, PIN state
│   │   └── branchStore.ts      # Active branch selection
│   │
│   ├── api/                    # API client functions (axios/fetch wrappers)
│   │   ├── client.ts           # Axios instance with interceptors
│   │   ├── auth.ts             # Auth API calls
│   │   ├── customers.ts        # Customer API calls
│   │   └── ...                 # (1 file ต่อ 1 module)
│   │
│   ├── types/                  # TypeScript type definitions
│   │   ├── auth.ts
│   │   ├── customer.ts
│   │   └── ...
│   │
│   ├── utils/                  # Utility functions
│   │   ├── formatters.ts       # Format date, currency, phone number
│   │   └── validators.ts       # Client-side validation helpers
│   │
│   └── styles/                 # Global styles
│       ├── globals.css         # CSS variables (design tokens)
│       └── fonts.css           # Font imports (Manrope, Inter)
│
├── tests/
│   └── fe/                     # Playwright test files
│
├── index.html                  # HTML template ที่ Vite ใช้
├── vite.config.ts              # Vite build configuration
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.ts          # Tailwind CSS configuration
├── playwright.config.ts        # Playwright test configuration
├── package.json                # Dependencies และ npm scripts
├── .env.example                # Template environment variables
└── README.md                   # ไฟล์นี้
```

---

## ขั้นตอนที่ 1 — Clone และเตรียม Project

```bash
# Clone repository
git clone <FE_REPO_URL> frontend
cd frontend
```

---

## ขั้นตอนที่ 2 — ติดตั้ง Dependencies

```bash
# ติดตั้ง Node.js packages ทั้งหมดจาก package.json
# npm install จะสร้าง folder node_modules/ และไฟล์ package-lock.json
npm install
```

ตรวจสอบว่าติดตั้งสำเร็จ:

```bash
# ควรแสดงรายชื่อ packages ที่ติดตั้งแล้ว
ls node_modules | head -20
```

---

## ขั้นตอนที่ 3 — ตั้งค่า Environment Variables

```bash
# คัดลอก template มาสร้างไฟล์ .env จริง
cp .env.example .env.local

# เปิดแก้ไข
nano .env.local
```

ค่าสำคัญที่ต้องแก้:

```env
# URL ของ BE API server
# ระหว่าง development ใช้ localhost
VITE_API_URL=http://localhost:8000

# ชื่อแอพ (แสดงใน browser tab)
VITE_APP_NAME=Studio Management
```

> **หมายเหตุ:** ใน Vite ทุก environment variable ที่จะใช้ใน code ต้องขึ้นต้นด้วย `VITE_` เสมอ

---

## ขั้นตอนที่ 4 — รัน Development Server

```bash
# รัน Vite development server
# จะเปิด browser อัตโนมัติที่ http://localhost:5173
npm run dev
```

Vite dev server มีคุณสมบัติ:
- **Hot Module Replacement (HMR):** แก้ code → browser อัปเดตทันทีโดยไม่ต้อง refresh
- **Fast startup:** เร็วกว่า Create React App มาก

เปิด browser ไปที่:
- **App:** http://localhost:5173

> **ต้องรัน BE server ด้วย** (ที่ port 8000) ถ้าต้องการ call API จริง

---

## ขั้นตอนที่ 5 — ติดตั้ง Playwright สำหรับ FE Tests

Playwright คือ framework สำหรับ automated browser testing ใช้รัน FE test cases

```bash
# ติดตั้ง Playwright และ browsers ที่จำเป็น
# คำสั่งนี้จะ download Chromium, Firefox, WebKit
npx playwright install
```

รัน tests:

```bash
# รัน FE test cases ทั้งหมด
npx playwright test

# รัน tests พร้อมดู browser (headed mode — เห็น browser เปิดจริงๆ)
npx playwright test --headed

# รัน test เฉพาะไฟล์
npx playwright test tests/fe/test_auth.py

# ดู test report หลังจากรัน
npx playwright show-report
```

---

## ขั้นตอนที่ 6 — Build สำหรับ Production

```bash
# Build FE เป็น static files พร้อม deploy
# output จะอยู่ใน folder dist/
npm run build

# Preview build ที่ได้ก่อน deploy (optional)
npm run preview
```

folder `dist/` ที่ได้จะถูก serve โดย Nginx ใน production

---

## Design System Reference

ดู `FE Design/azure_studio_pro/DESIGN.md` สำหรับรายละเอียดครบถ้วน

### Color Tokens (CSS Variables)
```css
/* globals.css */
:root {
  --color-primary: #162839;          /* Deep Sea — navigation, headers */
  --color-secondary: #395f94;        /* Steel Blue — interactive elements */
  --color-accent: #54b6b5;           /* Muted Teal — CTAs, success */
  --color-surface: #f8fafb;          /* Base canvas */
  --color-surface-low: #f2f4f5;      /* Secondary areas */
  --color-surface-lowest: #ffffff;   /* Cards */
  --color-on-surface: #191c1d;       /* Text (never pure black) */
  --color-on-surface-variant: #43474c; /* Secondary text */
}
```

### Key Design Rules
- ห้ามใช้ `1px solid border` สำหรับ section divider → ใช้ background color shift แทน
- Thai text ต้องมี `line-height: 1.6em` เสมอ
- Floating elements ใช้ Glassmorphism: `backdrop-blur: 12px`
- Shadow: `0px 20px 40px rgba(25,28,29,0.06)` เท่านั้น

---

## Quick Commands Reference

```bash
# รัน development server
npm run dev

# Build production
npm run build

# Preview production build
npm run preview

# รัน all FE tests
npx playwright test

# รัน tests แบบ headed (เห็น browser)
npx playwright test --headed

# ดู test report
npx playwright show-report

# Check TypeScript errors
npx tsc --noEmit

# Format code
npx prettier --write src/

# Lint code
npx eslint src/
```

---

## Troubleshooting

**Port 5173 ถูกใช้อยู่แล้ว:**
```bash
# เปลี่ยน port ใน vite.config.ts
# หรือรันด้วย port อื่น
npm run dev -- --port 3000
```

**API ต่อไม่ได้ (CORS error):**
```bash
# ตรวจสอบว่า BE server รันอยู่
curl http://localhost:8000/health

# ตรวจสอบ VITE_API_URL ใน .env.local
cat .env.local
```

**node_modules มีปัญหา:**
```bash
# ลบแล้วติดตั้งใหม่
rm -rf node_modules package-lock.json
npm install
```

**Playwright tests fail:**
```bash
# ติดตั้ง browsers ใหม่
npx playwright install

# ตรวจสอบว่า dev server รันอยู่ก่อนรัน tests
npm run dev &
npx playwright test
```
