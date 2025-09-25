#!/usr/bin/env python3
"""
Test Supabase connection with different approaches
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_direct_connection():
    """Test direct database connection"""
    print("🔄 Testing direct database connection...")

    try:
        import psycopg2

        # Connection parameters
        conn_params = {
            'host': 'db.lijtncazuwnbydeqtoyz.supabase.co',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'Mariaana953@7334',
            'sslmode': 'require',
            'connect_timeout': 15
        }

        print(f"Connecting to {conn_params['host']}:{conn_params['port']}")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Direct connection successful: {version[0][:50]}...")
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False

def test_pooler_connection():
    """Test pooler connection"""
    print("🔄 Testing pooler connection...")

    try:
        import psycopg2

        # Pooler connection parameters
        conn_params = {
            'host': 'aws-0-us-east-1.pooler.supabase.com',
            'port': 6543,
            'database': 'postgres',
            'user': 'postgres.lijtncazuwnbydeqtoyz',
            'password': 'Mariaana953@7334',
            'sslmode': 'require',
            'connect_timeout': 15
        }

        print(f"Connecting to {conn_params['host']}:{conn_params['port']}")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Pooler connection successful: {version[0][:50]}...")
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Pooler connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    print("🔄 Testing SQLAlchemy connection...")

    try:
        from sqlalchemy import create_engine, text

        # Try pooler first
        url = "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953@7334@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

        engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 15,
                "application_name": "transpontual_test",
                "sslmode": "require"
            }
        )

        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            print(f"✅ SQLAlchemy connection successful: {test_value}")

        engine.dispose()
        return True

    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Supabase connectivity...")
    print("=" * 50)

    # Test all connection methods
    results = []
    results.append(("Direct", test_direct_connection()))
    results.append(("Pooler", test_pooler_connection()))
    results.append(("SQLAlchemy", test_sqlalchemy_connection()))

    print("\n" + "=" * 50)
    print("📊 Results Summary:")
    for method, success in results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {method}: {status}")

    # Exit with appropriate code
    if any(success for _, success in results):
        print("\n🎉 At least one connection method works!")
        sys.exit(0)
    else:
        print("\n💥 All connection methods failed!")
        sys.exit(1)