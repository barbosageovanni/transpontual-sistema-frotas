# backend_fastapi/app/core/database.py
"""
Database configuration and helpers
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings


# Load database URL from settings (env/.env)
DATABASE_URL: str = get_settings().DATABASE_URL

# SQLAlchemy engine with improved timeout settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True,
    connect_args={
        "connect_timeout": 10,
        "application_name": "transpontual_api"
    } if "postgresql" in DATABASE_URL else {"timeout": 10},
    pool_size=3,
    max_overflow=5,
    pool_recycle=1800,  # 30 minutes
    pool_timeout=30,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency to provide a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create tables if they don't exist (blocking)."""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("DB: tables checked/created")


def test_connection() -> bool:
    """Try a simple connection to validate the DB URL."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:  # pragma: no cover
        print(f"DB connection error: {e}")
        return False
