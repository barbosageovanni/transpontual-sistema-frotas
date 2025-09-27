# backend_fastapi/app/core/database.py
"""
Database configuration and helpers
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings

# Load database URL from settings (env/.env)
import os
import socket

# CRITICAL: Apply IPv4-only patch for Render deployment
# This forces all connections to use A-records instead of AAAA (IPv6)
print("PATCH: Applying IPv4-only socket resolution for Render compatibility")
original_getaddrinfo = socket.getaddrinfo
def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """Force IPv4 resolution for Render environment compatibility"""
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

# Apply patch globally - do NOT restore original
socket.getaddrinfo = ipv4_only_getaddrinfo
print("PATCH: IPv4-only resolution active for entire application lifecycle")

# Try to get a working database URL
DATABASE_URL = None
DATABASE_AVAILABLE = False

def test_database_connection(url):
    """Test if database connection works"""
    try:
        from sqlalchemy import create_engine, text
        import time

        start_time = time.time()

        # IPv4 patch is already applied globally at module level

        # Create engine with Render-optimized settings
        connect_args = {
            "application_name": "transpontual_render_test",
            "options": "-c timezone=UTC"
        }

        # Add connect_timeout if not in URL
        if "connect_timeout" not in url:
            connect_args["connect_timeout"] = 30

        # Add SSL mode if not in URL
        if "sslmode" not in url and "postgresql" in url:
            connect_args["sslmode"] = "require"

        test_engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args=connect_args,
            pool_timeout=45,
            pool_recycle=1800,
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
            print(f"ERROR: Network unreachable - Render may be blocking external connections")
        elif "connection timed out" in error_msg.lower():
            print(f"ERROR: Connection timeout - host may be unreachable")
        elif "authentication failed" in error_msg.lower():
            print(f"ERROR: Authentication failed - check credentials")
        elif "ipv6" in error_msg.lower() or "address family" in error_msg.lower():
            print(f"ERROR: IPv6 connection issue - forcing IPv4")
        else:
            print(f"ERROR: DB test failed: {error_msg[:100]}...")
        return False

def get_working_database_url():
    """Get a working database URL with fallback"""
    global DATABASE_URL, DATABASE_AVAILABLE

    if DATABASE_URL and DATABASE_AVAILABLE:
        print(f"INFO: Using cached database connection")
        return DATABASE_URL

    settings = get_settings()

    # Check environment variables
    env_url = os.getenv('DATABASE_URL')
    print(f"ENV: DATABASE_URL from environment: {'SET' if env_url else 'NOT SET'}")
    print(f"ENV: Settings DATABASE_URL: {'SET' if settings.DATABASE_URL else 'NOT SET'}")

    # All possible database URLs to try (optimized for Render deployment with IPv4 patch)
    urls_to_try = [
        # Primary: Environment variable (should be set by Render)
        env_url,
        # HIGH PRIORITY: Pooler connections (better IPv4 routing for Render)
        "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=30",
        "postgresql://postgres:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=30",
        # Fallback: Direct Supabase connection with IPv4 patch
        "postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require&connect_timeout=30",
        "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require&connect_timeout=30",
        # Basic connection without query parameters
        "postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres",
        # Original from settings (final fallback)
        settings.DATABASE_URL,
    ]

    print(f"INFO: Testing {len([u for u in urls_to_try if u])} database URLs...")

    for i, url in enumerate(urls_to_try, 1):
        if url and url.strip():
            host = url.split('@')[1].split('/')[0] if '@' in url else 'unknown'
            print(f"TESTING {i}: Database connection to {host}")
            if test_database_connection(url):
                print(f"SUCCESS: Database connection {i} successful to {host}")
                DATABASE_URL = url
                DATABASE_AVAILABLE = True
                return url
            else:
                print(f"FAILED {i}: Database connection to {host}")

    print("ERROR: All database connections failed - running in offline mode")
    DATABASE_URL = settings.DATABASE_URL  # Fallback to original
    DATABASE_AVAILABLE = False
    return DATABASE_URL

# Get working database URL
DATABASE_URL = get_working_database_url()

# SQLAlchemy engine with Render optimized settings
if "postgresql" in DATABASE_URL:
    connect_args = {
        "application_name": "transpontual_api_render",
        "options": "-c timezone=UTC"
    }
    # Add connect_timeout if not in URL
    if "connect_timeout" not in DATABASE_URL:
        connect_args["connect_timeout"] = 30
    # Add SSL mode if not in URL
    if "sslmode" not in DATABASE_URL:
        connect_args["sslmode"] = "require"
else:
    connect_args = {"timeout": 30}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_size=2,
    max_overflow=3,
    pool_recycle=1800,  # 30 minutes for better connection management
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
        try:
            db.rollback()
        except Exception as rollback_error:
            print(f"ERROR: Failed to rollback session: {rollback_error}")
        raise
    finally:
        try:
            db.close()
        except Exception as close_error:
            print(f"ERROR: Failed to close session: {close_error}")

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
