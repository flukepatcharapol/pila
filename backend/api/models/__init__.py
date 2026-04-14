"""
api/models/__init__.py

Export all SQLAlchemy models เพื่อให้ conftest และ alembic import ได้ในที่เดียว
import ทุก model ที่นี่เพื่อให้ Base.metadata รู้จัก table ทั้งหมดก่อน create_all()
"""
from api.models.partner import Partner
from api.models.branch import Branch
from api.models.user import (
    User, SourceType, UserRole,
    LoginAttempt, PinAttempt, PinOtp, PasswordResetToken, UserSession,
    PasswordSession,
)
from api.models.customer import Customer, CustomerHourBalance, CustomerCodeCounter
from api.models.customer_hour import CustomerHourLog
from api.models.trainer import Trainer, Caretaker
from api.models.package import Package, PackageBranchScope
from api.models.order import Order, OrderPayment
from api.models.booking import Booking, CancelPolicy
from api.models.permission import PermissionMatrix, FeatureToggle
from api.models.activity_log import ActivityLog
from api.models.google_integration import GoogleToken, SignaturePrintFile, UserPreference

__all__ = [
    "Partner",
    "Branch",
    "User",
    "SourceType",
    "UserRole",
    "LoginAttempt",
    "PinAttempt",
    "PinOtp",
    "PasswordResetToken",
    "UserSession",
    "PasswordSession",
    "Customer",
    "CustomerHourBalance",
    "CustomerCodeCounter",
    "CustomerHourLog",
    "Trainer",
    "Caretaker",
    "Package",
    "PackageBranchScope",
    "Order",
    "OrderPayment",
    "Booking",
    "CancelPolicy",
    "PermissionMatrix",
    "FeatureToggle",
    "ActivityLog",
    "GoogleToken",
    "SignaturePrintFile",
    "UserPreference",
]
