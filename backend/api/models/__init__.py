"""
api/models/__init__.py

Export all SQLAlchemy models เพื่อให้ conftest และ alembic import ได้ในที่เดียว
"""
from api.models.partner import Partner
from api.models.branch import Branch
from api.models.user import User, SourceType
from api.models.customer import Customer, CustomerHourBalance
from api.models.trainer import Trainer, Caretaker
from api.models.package import Package
from api.models.order import Order
from api.models.booking import Booking

__all__ = [
    "Partner",
    "Branch",
    "User",
    "SourceType",
    "Customer",
    "CustomerHourBalance",
    "Trainer",
    "Caretaker",
    "Package",
    "Order",
    "Booking",
]
