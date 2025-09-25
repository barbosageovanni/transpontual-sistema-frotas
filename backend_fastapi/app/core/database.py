# backend_fastapi/app/core/database.py
"""
Database configuration and helpers
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings


# Load database URL from settings (env/.env)
import os

# Try to get a working database URL
DATABASE_URL = None
DATABASE_AVAILABLE = False

def test_database_connection(url):
    """Test if database connection works"""
    try:
        from sqlalchemy import create_engine
        test_engine = create_engine(
            url,
            connect_args={
                "connect_timeout": 10,
                "sslmode": "require" if "postgresql" in url else None
            }
        )
        connection = test_engine.connect()
        connection.close()
        return True
    except Exception as e:
        print(f"❌ DB test failed for {url.split('@')[1].split('/')[0] if '@' in url else 'url'}: {str(e)[:50]}...")
        return False

def get_working_database_url():
    """Get a working database URL with fallback"""
    global DATABASE_URL, DATABASE_AVAILABLE

    if DATABASE_URL and DATABASE_AVAILABLE:
        return DATABASE_URL

    settings = get_settings()

    # All possible database URLs to try
    urls_to_try = [
        settings.DATABASE_URL,
        "postgresql://postgres:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require",
        "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres",
    ]

    for url in urls_to_try:
        if url and url.strip():
            print(f"🔄 Testing database: {url.split('@')[1].split('/')[0] if '@' in url else 'unknown'}")
            if test_database_connection(url):
                print(f"✅ Database connection successful!")
                DATABASE_URL = url
                DATABASE_AVAILABLE = True
                return url

    print("❌ All database connections failed - running in offline mode")
    DATABASE_URL = settings.DATABASE_URL  # Fallback to original
    DATABASE_AVAILABLE = False
    return DATABASE_URL

# Get working database URL
DATABASE_URL = get_working_database_url()

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
    if not DATABASE_AVAILABLE:
        # Return a mock database session for offline mode
        print("⚠️ Using offline mode - no database operations available")
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"❌ Database session error: {e}")
        db.rollback()
        yield None
    finally:
        try:
            db.close()
        except:
            pass


def is_database_available():
    """Check if database is available"""
    return DATABASE_AVAILABLE


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
