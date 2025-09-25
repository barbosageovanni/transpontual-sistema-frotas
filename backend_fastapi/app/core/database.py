# backend_fastapi/app/core/database.py
"""
Database configuration and helpers
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings


# Load database URL from settings (env/.env)
import os

def get_database_url():
    """Get database URL with fallback options for Railway"""
    settings = get_settings()
    primary_url = settings.DATABASE_URL

    # Try alternative URLs if primary fails
    backup_urls = os.getenv('DATABASE_BACKUP_URLS', '').split('|')

    all_urls = [primary_url] + [url for url in backup_urls if url.strip()]

    for url in all_urls:
        if url.strip():
            try:
                print(f"🔄 Trying database connection: {url.split('@')[1].split('/')[0] if '@' in url else 'unknown'}")
                test_engine = create_engine(url, connect_args={"connect_timeout": 5})
                test_engine.connect()
                print(f"✅ Database connection successful!")
                return url
            except Exception as e:
                print(f"❌ Connection failed: {str(e)[:100]}...")
                continue

    print(f"⚠️ All database connections failed, using primary URL")
    return primary_url

DATABASE_URL: str = get_database_url()

# SQLAlchemy engine with Railway optimized settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True,
    connect_args={
        "connect_timeout": 30,
        "application_name": "transpontual_api_railway",
        "sslmode": "require"
    } if "postgresql" in DATABASE_URL else {"timeout": 30},
    pool_size=2,
    max_overflow=3,
    pool_recycle=3600,  # 1 hour
    pool_timeout=45,
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
