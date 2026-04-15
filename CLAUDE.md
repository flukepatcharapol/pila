# CLAUDE.md — Pila Studio Management

## Project Context

**Tech Stack:** 
- BE: FastAPI (Python) + PostgreSQL + SQLAlchemy
- FE: React/Vue + TypeScript + Vite
- Tests: pytest (BE) + Playwright (FE)
- Current focus: Auth dual-session implementation (v0.3)

**Key Links:**
- Design doc: `docs/auth_dual_session_design.md` (opaque password session + 6h access JWT)
- Test plan: `docs/06_automation_test_plan.md` (test isolation, --keep-db flag)
- Implementation checklist: section 12 of design doc

---

## Working Style Preferences

### 1. Parallel Task Detection (CRITICAL)

**Always ask:** When user gives task(s), detect if independent tasks can run parallel.

**Pattern:** Multiple tracks (BE, FE, Tests, different modules) often can run parallel even if they look sequential.

**Action:**
- List task dependencies explicitly
- Ask: "These 3 can run parallel: X, Y, Z. Want dispatch?"
- Show blocking relationships if any
- Get user approval before creating single dispatch or multiple agents

**Why:** Maximize AI dispatch efficiency (4-7 hrs vs 1-2 weeks for humans).

### 2. Task Tracking (IN MEMORY, NOT CLAUDE.md)

- Session context → memory files (auto-clear after session ends)
- Permanent rules → CLAUDE.md (persists across sessions)
- DO NOT duplicate task lists in both places

**Current tasks:**
- Auth dual-session dispatch: 3 tracks (BE → FE+Test parallel)
  - Status: awaiting "Start dispatch" from user
  - Implementation checklist in design doc, section 12

### 3. Code Style & Quality

**Preferences:**
- No unnecessary abstractions (one-time ops stay inline)
- Don't add features beyond what's asked
- Don't refactor surrounding code unless asked
- Prefer editing files over creating new ones
- Tests must verify both API response AND DB state (dual assertions)

**Testing philosophy:**
- High Risk tests (mutate seed data) → reset with autouse fixture
- Medium Risk tests (state affects subsequent runs) → isolated_last marker + 2-command run
- All 204 BE tests passing; --keep-db flag for manual inspection

### 4. Git & Commits

- Always create NEW commits (never amend unless explicitly asked)
- Ask before force-push, destructive operations, shared system changes
- Commit message: clear "why", not just "what"
- Co-author: `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>`

---

## Current Implementation Status

### ✅ Completed
- Test isolation strategy (--keep-db flag, isolated_last marker)
- Auth design doc v0.3 (error_code responses, frontend modal flows, 3 sequence diagrams)
- Documentation: 06_automation_test_plan.md + BE_README.md updated
- **Auth Dual-Session — Phase 1 BE** (2026-04-14)
  - PasswordSession model + Alembic migration (c01ad1b96c63)
  - auth.py: login→opaque token, pin_verify→6h JWT, logout/change_password revoke sessions
  - dependencies/auth.py: verify_password_session (SHA-256 lookup)
  - routers/auth.py: wired verify_password_session dependency
  - config.py: PASSWORD_SESSION_DAYS=30, PIN_ACCESS_TOKEN_EXPIRE_MINUTES=360
- **Auth Dual-Session — Phase 2 FE** (2026-04-14)
  - frontend/src/lib/auth.ts: session storage helpers
  - frontend/src/api/client.ts: 401 interceptor + redirect logic
  - frontend/src/pages/Login.tsx + Pin.tsx + Dashboard.tsx
  - frontend/src/components/SessionExpiredModal.tsx (Thai modal)
  - frontend/src/App.tsx: routing + modal wiring
- **Auth Dual-Session — Phase 2 Tests** (2026-04-14)
  - 10 new DS test cases (DS-01 to DS-10) in test_auth_api.py
  - 2 new fixtures: password_session_via_login, full_auth_via_api
  - **204 BE tests passing** (was 192 before auth dispatch)
- **Auth Dual-Session — Phase 3 FE Tests** (2026-04-15)
  - Added `data-testid` attributes to Login.tsx, Pin.tsx, Dashboard.tsx, SessionExpiredModal.tsx
  - Added `ProtectedRoute` component in App.tsx (guards /dashboard, redirects to /pin or /login)
  - Rewrote tests/fe/test_auth.py: 10 tests (TC-AUTH-01–06 + TC-FE-DS-01–07)
  - Added dual-session helpers to tests/fe/helpers/common_web.py
  - Removed old sessionStorage.setItem('pin_expired', 'true') hack
  - Updated auth_dual_session_design.md: checklist all ✅

### ⏳ Next: Run FE Tests + Human Review
- Run FE Playwright tests: `pytest tests/fe/test_auth.py` (10 tests)
- Fix any failures (FE server must be running at localhost:5173)
- Review all changes: BE + FE + Tests + Design doc
- Pipeline now at Step 16 (FE + E2E Tests Pass)

### 🔮 Future (post-v1)
- Build full FE system (15+ screens — only auth flow exists now)
- Single-device logout (per password_session revoke)
- httpOnly cookie for password session (XSS mitigation)
- Session status endpoint
- FE Playwright tests for all feature screens

---

## Dispatch Rules

### When to suggest dispatch
- Multiple independent tasks → ask if user wants parallel agents
- Long implementation checklist → break into phases + dispatch
- BE/FE/Tests in same epic → check dependencies first

### How to create dispatch
- Use `/anthropic-skills:create-dispatch-list` skill
- OR ask user "Want me to start dispatch?" + show proposed tracks
- Map dependencies → show which tasks block which

### What dispatch does
- Creates N independent Claude agents (max parallelization)
- Each agent works on one track in isolation
- Agents report back with PRs/code ready to merge
- No manual copy-paste needed (fully automated)

---

## Contact & Handoff

**If context is lost or session expires:**
- Check CLAUDE.md (this file) for permanent context
- Check memory/ folder for session-specific notes
- All tasks in dispatch list are stored as plain Markdown

**For human team members:**
- PR review checklist in each dispatch task
- Code ready for merge (AI 80%, human review 20%)
- Estimated review time: 30 min per track

---

## Version & Last Updated

- **v1.0** — 2026-04-14 — Initial setup, auth dispatch pending
- **v1.1** — 2026-04-14 — Auth dual-session fully implemented (BE + FE + Tests)
- **v1.2** — 2026-04-15 — Phase 3: data-testids, ProtectedRoute, FE Playwright tests (TC-FE-DS-01–07)
- **Status:** FE Playwright tests ready to run — `pytest tests/fe/test_auth.py`
