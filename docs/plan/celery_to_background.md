# Celery to FastAPI BackgroundTasks Migration Plan (Single-File Final)

## Objective

Migrate from unused Celery worker setup to FastAPI `BackgroundTasks` with one DB table for task tracking/status, for current async candidates:

- `POST /orders/{order_id}/receipt`
- `POST /signature-print/generate`

This document includes:
- Codebase research findings
- Architecture decision
- Before/after examples
- Exact file-level change plan
- Risks and mitigations
- Test and rollout plan

---

## Current Codebase Findings

### 1) Celery runtime is configured but not actually wired
- `docker-compose.yml` defines a `worker` service with Celery command:
  - `uv run celery -A worker.celery_app worker --loglevel=info`
- But there is no `worker` package/module in `backend` to back this command.
- No Celery task definitions or dispatch calls were found (`@shared_task`, `.delay()`, `apply_async()`).

### 2) Async candidates are TODOs only
- `backend/api/routers/orders.py`:
  - `/orders/{order_id}/receipt` contains TODO for Celery email.
- `backend/api/routers/signature_print.py`:
  - `/signature-print/generate` contains TODO for Celery Google Sheet generation.

### 3) Request DB session lifecycle warning (critical)
- `backend/api/database.py` closes request-scoped DB session after response.
- Background jobs must not use request `db` dependency object.

---

## Architecture Decision

Use FastAPI `BackgroundTasks` now, with one table (`background_tasks`) for lifecycle tracking and retries.

### Why this is enough now
- No active Celery usage in current app logic.
- Async workload scope is currently small.
- Faster implementation and simpler operations.

### Known tradeoff
- `BackgroundTasks` are in-process; restart/crash can interrupt jobs.
- Mitigation: DB status + recovery scan on startup + retries.

---

## Mandatory Review Adjustments (from code review)

1. **Fresh DB session inside background execution**
   - Each task run must open/close its own `SessionLocal()`.

2. **Startup recovery + stale job handling**
   - On app startup, recover `queued/running/retrying` jobs.
   - Requeue eligible jobs by retry policy.

3. **API contract migration handling**
   - Existing immediate-success responses become `202 + task_id`.
   - Coordinate FE and tests in same release (or feature-flag response mode).

4. **Idempotency for side-effect tasks**
   - Enforce idempotency key for email/send/generate.
   - Deduplicate repeated trigger requests.

5. **Infra/package cleanup completeness**
   - Remove worker service, worker copy, Celery dep references.
   - Ensure docs/tests reflect final architecture.

---

## Before -> After (Codebase Style)

## A) Orders receipt endpoint

### Before (`backend/api/routers/orders.py`)
```python
@router.post("/orders/{order_id}/receipt")
def resend_receipt(
    order_id: UUID,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    from api.models.order import Order
    from fastapi import HTTPException

    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # TODO: ส่ง email จริงผ่าน Celery task ใน production
    return {"message": "Receipt sent", "order_id": str(order_id)}
```

### After (proposed)
```python
from fastapi import BackgroundTasks, HTTPException, status
from api.services.background_tasks import enqueue_task, run_task

@router.post("/orders/{order_id}/receipt", status_code=status.HTTP_202_ACCEPTED)
def resend_receipt(
    order_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    from api.models.order import Order

    order = db.query(Order).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    task_id = enqueue_task(
        db=db,
        task_type="receipt_send",
        entity_type="order",
        entity_id=str(order_id),
        payload={"order_id": str(order_id)},
        created_by=current_user.get("sub"),
        idempotency_key=f"receipt:{order_id}",
    )
    background_tasks.add_task(run_task, task_id)

    return {"task_id": str(task_id), "status": "queued"}
```

## B) Signature print generation endpoint

### Before (`backend/api/routers/signature_print.py`)
```python
# TODO: ใน production ให้ส่ง task ไป Celery สร้าง Google Sheet จริง
# ตอนนี้สร้าง mock file record
mock_file_id = f"mock_file_{order_id}_{int(datetime.utcnow().timestamp())}"
mock_url = f"https://docs.google.com/spreadsheets/d/{mock_file_id}"

file_record = SignaturePrintFile(
    order_id=order_id,
    generated_by=user_id,
    file_url=mock_url,
    file_id=mock_file_id,
)
db.add(file_record)
db.flush()

return _file_to_dict(file_record)
```

### After (proposed)
```python
@router.post("/signature-print/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_signature_print(
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    # validate user/order/google token as before...

    task_id = enqueue_task(
        db=db,
        task_type="signature_generate",
        entity_type="order",
        entity_id=str(order_id),
        payload={"order_id": str(order_id), "user_id": str(user_id)},
        created_by=current_user.get("sub"),
        idempotency_key=f"signature:{order_id}:{user_id}",
    )
    background_tasks.add_task(run_task, task_id)

    return {"task_id": str(task_id), "status": "queued"}
```

## C) New DB model for tracking

### After (new file `backend/api/models/background_task.py`)
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base

class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", index=True)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

## D) New task runner service

### After (new file `backend/api/services/background_tasks.py`)
```python
from datetime import datetime
from api.database import SessionLocal
from api.models.background_task import BackgroundTask

def enqueue_task(db, task_type, entity_type, entity_id, payload, created_by=None, idempotency_key=None):
    task = BackgroundTask(
        task_type=task_type,
        status="queued",
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
        created_by=created_by,
        idempotency_key=idempotency_key,
    )
    db.add(task)
    db.flush()
    return task.id

def run_task(task_id):
    db = SessionLocal()  # critical: fresh session, not request-scoped session
    try:
        task = db.query(BackgroundTask).filter_by(id=task_id).first()
        if not task:
            return

        task.status = "running"
        task.started_at = datetime.utcnow()
        task.attempt_count += 1
        db.flush()

        if task.task_type == "receipt_send":
            # call email sender service
            pass
        elif task.task_type == "signature_generate":
            # call signature generation service
            pass

        task.status = "success"
        task.result = {"ok": True}
        task.finished_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        task = db.query(BackgroundTask).filter_by(id=task_id).first()
        if task:
            task.error_message = str(exc)
            if task.attempt_count >= task.max_attempts:
                task.status = "failed"
            else:
                task.status = "retrying"
                # set next_retry_at with backoff
            task.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
```

## E) Compose/infra cleanup

### Before (`docker-compose.yml`)
```yaml
worker:
  build:
    context: ./backend
    dockerfile: Dockerfile
  command: ["uv", "run", "celery", "-A", "worker.celery_app", "worker", "--loglevel=info"]
```

### After (proposed)
```yaml
# remove worker service (no Celery runtime)
```

---

## File-Level Change Checklist

## Existing files to update
- `backend/api/routers/orders.py`
- `backend/api/routers/signature_print.py`
- `backend/api/main.py` (register new task-status router)
- `backend/api/models/__init__.py` (export model)
- `docker-compose.yml`
- `backend/Dockerfile`
- `backend/pyproject.toml`
- `backend/README.md` (runtime docs)

## New files to add
- `backend/api/models/background_task.py`
- `backend/api/schemas/background_task.py`
- `backend/api/services/background_tasks.py`
- `backend/api/routers/background_tasks.py`
- Alembic migration file for `background_tasks` table

---

## DB Table Spec (Final)

Table: `background_tasks`

Columns:
- `id` UUID PK
- `task_type` VARCHAR(50), indexed
- `status` VARCHAR(20), indexed
- `entity_type` VARCHAR(50), indexed
- `entity_id` VARCHAR(64), indexed
- `payload` JSONB
- `result` JSONB nullable
- `error_message` TEXT nullable
- `attempt_count` INT default 0
- `max_attempts` INT default 3
- `next_retry_at` TIMESTAMP nullable
- `idempotency_key` VARCHAR(120) unique nullable
- `created_by` UUID nullable
- `created_at` TIMESTAMP
- `started_at` TIMESTAMP nullable
- `finished_at` TIMESTAMP nullable
- `updated_at` TIMESTAMP

Indexes:
- `(status, next_retry_at)`
- `(entity_type, entity_id, created_at DESC)`
- `(task_type, created_at DESC)`

---

## API Contract Plan

## Endpoint behavior
- `POST /orders/{order_id}/receipt` -> `202 Accepted` with `task_id`
- `POST /signature-print/generate` -> `202 Accepted` with `task_id`

## New status endpoints
- `GET /background-tasks/{task_id}`
- `GET /background-tasks?entity_type=&entity_id=&status=&task_type=`

## Compatibility strategy
Pick one:
1. Feature flag for old vs new response shape, or
2. Coordinated release with FE/tests updated in same PR/release window.

---

## Recovery, Retry, and Reliability Rules

- On startup, recover stale tasks (`queued`, `running`, `retrying`) based on timeout/retry policy.
- Exponential backoff (e.g. 10s, 30s, 120s) using `next_retry_at`.
- Mark final `failed` after `attempt_count >= max_attempts`.
- Enforce idempotency for external side effects.
- Log all state transitions with task id and type.

---

## Security and Access Control

- Keep `require_pin_verified` on enqueue endpoints.
- Restrict task status visibility to authorized users/scopes.
- Do not store secrets in task payload/result.
- Sanitize `error_message` for client-safe exposure.

---

## Testing Plan

## Unit tests
- enqueue behavior
- transition lifecycle
- retry and terminal failure
- idempotency duplicate handling

## API tests
- enqueue returns `202` + `task_id`
- status endpoint fields are accurate
- permission checks for task visibility

## Integration tests
- mock email/google providers
- success/failure persistence
- startup recovery behavior

## Regression tests
- existing order/signature auth and validation unchanged
- FE flow updated for async status polling if required

---

## Rollout Plan

1. Add model + migration + service + status router.
2. Implement enqueue flow in `orders` receipt endpoint.
3. Implement enqueue flow in `signature-print` generation endpoint.
4. Add startup recovery scanner.
5. Update FE/tests for `202 + task_id`.
6. Remove worker/Celery runtime references.
7. Run full test suites and smoke tests.
8. Deploy gradually (feature flag if used).

---

## Rollback Plan

- Re-enable old synchronous placeholder responses.
- Keep `background_tasks` table (non-breaking).
- If needed, reintroduce Celery runtime in separate follow-up.

---

## Acceptance Criteria

- No runtime Celery dependency required.
- Async endpoints return `202` with trackable `task_id`.
- Task lifecycle persisted and queryable.
- Restart/retry behavior is defined and test-covered.
- Existing auth/permissions remain intact.
