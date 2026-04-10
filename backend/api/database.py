from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from api.config import settings


engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — ให้ DB session ต่อ request
    ปิด session อัตโนมัติหลัง request เสร็จ (ป้องกัน connection leak)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
