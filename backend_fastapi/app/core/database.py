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
        from sqlalchemy import create_engine, text
        import time

        start_time = time.time()

        # Create engine with IPv4-optimized settings
        test_engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10,
                "application_name": "transpontual_render",
                "sslmode": "require" if "postgresql" in url else None,
                "options": "-c timezone=UTC",
                # Force IPv4 if possible
                "host": url.split('@')[1].split(':')[0] if '@' in url else None
            },
            pool_timeout=15,
            pool_recycle=300,
            echo=False
        )

        # Test actual connection
        with test_engine.connect() as connection:
            # Simple query to verify connection works
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.scalar()

        connection_time = time.time() - start_time
        print(f"SUCCESS: Connection successful in {connection_time:.2f}s (result: {test_value})")

        test_engine.dispose()
        return True

    except Exception as e:
        error_msg = str(e)
        if "network is unreachable" in error_msg.lower():
            print(f"ERROR: Network unreachable - Railway may be blocking external connections")
        elif "connection timed out" in error_msg.lower():
            print(f"ERROR: Connection timeout - host may be unreachable")
        elif "authentication failed" in error_msg.lower():
            print(f"ERROR: Authentication failed - check credentials")
        else:
            print(f"ERROR: DB test failed: {error_msg[:100]}...")
        return False

def get_working_database_url():
    """Get a working database URL with fallback"""
    global DATABASE_URL, DATABASE_AVAILABLE

    if DATABASE_URL and DATABASE_AVAILABLE:
        return DATABASE_URL

    settings = get_settings()

    # All possible database URLs to try (IPv4 prioritized)
    urls_to_try = [
        # IPv4 pooler connections (best for cloud deployment)
        "postgresql://postgres:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=10",
        "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=10",
        # Pooler with port 6543 (transaction mode)
        "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require&connect_timeout=10",
        # Direct connection (may have IPv6 issues)
        "postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require&connect_timeout=10",
        # Original from settings
        settings.DATABASE_URL,
    ]

    for url in urls_to_try:
        if url and url.strip():
            print(f"TESTING: Database connection: {url.split('@')[1].split('/')[0] if '@' in url else 'unknown'}")
            if test_database_connection(url):
                print(f"SUCCESS: Database connection successful!")
                DATABASE_URL = url
                DATABASE_AVAILABLE = True
                return url

    print("ERROR: All database connections failed - running in offline mode")
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
        print("WARNING: Using offline mode - no database operations available")
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"ERROR: Database session error: {e}")
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
