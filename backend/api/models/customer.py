from sqlalchemy import String, Integer, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_id: Mapped[int] = mapped_column(Integer, ForeignKey("branches.id"))
    source_type_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("source_types.id"), nullable=True)


class CustomerHourBalance(Base):
    __tablename__ = "customer_hour_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"))
    balance_hours: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
