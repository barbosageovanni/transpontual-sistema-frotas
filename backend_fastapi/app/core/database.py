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
        import socket

        start_time = time.time()

        # Force IPv4 resolution for Render deployment
        original_getaddrinfo = socket.getaddrinfo
        def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

        socket.getaddrinfo = ipv4_only_getaddrinfo

        # Create engine with Render-optimized settings
        test_engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 30,
                "application_name": "transpontual_render_test",
                "sslmode": "require" if "postgresql" in url else None,
                "options": "-c timezone=UTC",
                "tcp_keepalives_idle": "10",
                "tcp_keepalives_interval": "5",
                "tcp_keepalives_count": "3"
            },
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

        # Restore original getaddrinfo
        socket.getaddrinfo = original_getaddrinfo
        return True

    except Exception as e:
        # Restore original getaddrinfo on error
        socket.getaddrinfo = original_getaddrinfo

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

    # All possible database URLs to try (optimized for Render deployment)
    urls_to_try = [
        # Primary: Environment variable (should be set by Render)
        env_url,
        # Fallback: Direct Supabase connection with optimized settings for Render
        "postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require&connect_timeout=30&tcp_keepalives_idle=10&tcp_keepalives_interval=5&tcp_keepalives_count=3",
        "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require&connect_timeout=30&tcp_keepalives_idle=10",
        # Alternative: Pooler connections (may have better routing for Render)
        "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=30",
        "postgresql://postgres:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=30",
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
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True,
    connect_args={
        "connect_timeout": 30,
        "application_name": "transpontual_api_render",
        "sslmode": "require",
        "tcp_keepalives_idle": "10",
        "tcp_keepalives_interval": "5",
        "tcp_keepalives_count": "3"
    } if "postgresql" in DATABASE_URL else {"timeout": 30},
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
