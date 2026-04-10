from sqlalchemy import Integer, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from api.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"))
    trainer_id: Mapped[int] = mapped_column(Integer, ForeignKey("trainers.id"))
    hours_deducted: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    session_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
