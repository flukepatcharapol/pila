from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from api.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"))
    package_id: Mapped[int] = mapped_column(Integer, ForeignKey("packages.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
