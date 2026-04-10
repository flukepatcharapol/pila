// playwright.config.ts
//
// Playwright configuration สำหรับ FE automated tests
// วางไฟล์นี้ไว้ที่ root ของ frontend/ project
// รัน tests ด้วย: npx playwright test  หรือ  pytest tests/fe/ (ผ่าน pytest-playwright)
// เหตุผล: config ที่เดียวทำให้ทุก browser และ CI ใช้ settings เดียวกัน

import { defineConfig, devices } from "@playwright/test";

// อ่าน FE_BASE_URL จาก environment variable
// ถ้าไม่มีให้ใช้ localhost:5173 (Vite default)
const baseURL = process.env.FE_BASE_URL || "http://localhost:5173";

export default defineConfig({
  // ─── Test Discovery ────────────────────────────────────────────────────────────

  // Playwright จะหา test files จาก folder tests/fe/
  testDir: "./tests/fe",

  // pattern สำหรับหา test files
  testMatch: "**/*.py", // Python tests ผ่าน pytest-playwright

  // ─── Timeouts ──────────────────────────────────────────────────────────────────

  // timeout ของแต่ละ test (30 วินาที)
  // เพิ่มถ้า server เปิดช้าหรือ network ช้า
  timeout: 30_000,

  // timeout สำหรับ expect assertions (5 วินาที)
  // เช่น expect(page.locator('...').toBeVisible() จะรอสูงสุด 5 วินาที
  expect: {
    timeout: 5_000,
  },

  // ─── Retry ─────────────────────────────────────────────────────────────────────

  // retry 2 ครั้งถ้า test fail ใน CI environment
  // ป้องกัน flaky tests จาก network หรือ timing issues
  retries: process.env.CI ? 2 : 0,

  // จำนวน workers (parallel tests) ใน CI ใช้ 1 เพื่อลด resource usage
  workers: process.env.CI ? 1 : undefined,

  // ─── Reporter ──────────────────────────────────────────────────────────────────

  reporter: [
    // แสดงผลใน terminal แบบ list
    ["list"],
    // สร้าง HTML report ที่ playwright-report/index.html
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],

  // ─── Global Settings ───────────────────────────────────────────────────────────

  use: {
    // Base URL สำหรับ page.goto('/customers') → http://localhost:5173/customers
    baseURL,

    // เก็บ screenshot เมื่อ test fail (ช่วย debug)
    screenshot: "only-on-failure",

    // เก็บ video เมื่อ test fail (ช่วย debug)
    video: "retain-on-failure",

    // เก็บ trace เมื่อ test fail (ใช้ npx playwright show-trace)
    trace: "retain-on-failure",

    // ขนาด browser window (desktop-first design)
    viewport: { width: 1440, height: 900 },

    // locale ไทย สำหรับ date formatting และ Thai text
    locale: "th-TH",

    // timezone ไทย
    timezoneId: "Asia/Bangkok",
  },

  // ─── Projects (Browsers) ───────────────────────────────────────────────────────

  projects: [
    // Chromium (Chrome, Edge) — primary browser
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },

    // Firefox — secondary browser สำหรับ cross-browser testing
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },

    // WebKit (Safari) — สำหรับ macOS/iOS compatibility
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },

    // Tablet viewport สำหรับ responsive testing
    // แอพออกแบบเป็น desktop/tablet-first
    {
      name: "tablet",
      use: {
        ...devices["iPad Pro"],
        viewport: { width: 1024, height: 768 },
      },
    },
  ],

  // ─── Dev Server ────────────────────────────────────────────────────────────────

  // รัน Vite dev server อัตโนมัติก่อน tests
  // ถ้า server รันอยู่แล้ว Playwright จะ reuse ได้เลย
  webServer: {
    // คำสั่ง start Vite dev server
    command: "npm run dev",

    // รอให้ server พร้อมที่ URL นี้ก่อนรัน tests
    url: baseURL,

    // reuse server ที่รันอยู่แล้ว (ประหยัดเวลา)
    reuseExistingServer: !process.env.CI,

    // timeout รอ server start (60 วินาที)
    timeout: 60_000,
  },
});
