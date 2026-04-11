from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings

# ─── Import routers ────────────────────────────────────────────────────────────
from api.routers.auth import router as auth_router
from api.routers.customers import router as customers_router
from api.routers.orders import router as orders_router
from api.routers.users import router as users_router
from api.routers.bookings import router as bookings_router
from api.routers.activity_log import router as activity_log_router
from api.routers.permissions import router as permissions_router
from api.routers.customer_hours import router as customer_hours_router
from api.routers.dashboard import router as dashboard_router
from api.routers.packages import router as packages_router
from api.routers.trainers import router as trainers_router
from api.routers.branches import router as branches_router
from api.routers.caretakers import router as caretakers_router
from api.routers.validation import router as validation_router
from api.routers.integrity import router as integrity_router
from api.routers.google_settings import router as google_settings_router
from api.routers.signature_print import router as signature_print_router
from api.routers.security import router as security_router
from api.routers.cancel_policy import router as cancel_policy_router
from api.routers.help import router as help_router

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check — ใช้สำหรับ docker healthcheck และ monitoring"""
    return {"status": "ok"}


# ─── Register routers ─────────────────────────────────────────────────────────
app.include_router(auth_router, tags=["auth"])
app.include_router(customers_router, tags=["customers"])
app.include_router(orders_router, tags=["orders"])
app.include_router(users_router, tags=["users"])
app.include_router(bookings_router, tags=["bookings"])
app.include_router(activity_log_router, tags=["activity_log"])
app.include_router(permissions_router, tags=["permissions"])
app.include_router(customer_hours_router, tags=["customer_hours"])
app.include_router(dashboard_router, tags=["dashboard"])
app.include_router(packages_router, tags=["packages"])
app.include_router(trainers_router, tags=["trainers"])
app.include_router(branches_router, tags=["branches"])
app.include_router(caretakers_router, tags=["caretakers"])
app.include_router(validation_router, tags=["validation"])
app.include_router(integrity_router, tags=["integrity"])
app.include_router(google_settings_router, tags=["settings"])
app.include_router(signature_print_router, tags=["signature_print"])
app.include_router(security_router, tags=["security"])
app.include_router(cancel_policy_router, tags=["settings"])
app.include_router(help_router, tags=["help"])
