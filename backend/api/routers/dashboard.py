"""
api/routers/dashboard.py

Dashboard endpoint:
  GET /dashboard   — aggregate data ตาม role + time range
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_pin_verified
from api.services import dashboard as dashboard_service

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(
    range: str = Query("today", description="today|week|month|custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(require_pin_verified),
    db: Session = Depends(get_db),
):
    """
    Dashboard data ตาม role:
      trainer      → hours trained, customer count, bookings
      admin        → orders today, hours deducted today
      branch_master → total orders, revenue, outstanding
      owner        → branch_master view + all branches
      developer    → owner view + cross-partner
    """
    return dashboard_service.get_dashboard(
        current_user, db,
        range_type=range,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )
