from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
