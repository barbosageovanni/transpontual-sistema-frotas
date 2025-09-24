#!/usr/bin/env python3
"""
FRONTEND ONLY - Force Flask Dashboard execution
"""
import os
import sys
from pathlib import Path

print("🎨 FRONTEND DASHBOARD STARTUP")
print("=" * 60)
print("This script ONLY starts Flask Dashboard - NOT FastAPI!")
print("=" * 60)

# Configure environment for frontend
api_base_from_env = os.getenv('API_BASE')
if not api_base_from_env:
    # Point to backend service
    api_base = 'https://web-production-256fe.up.railway.app'
    os.environ.setdefault('API_BASE', api_base)
    print(f"🔗 API_BASE set to: {api_base}")

os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'False')

# Add flask_dashboard to Python path
dashboard_dir = Path(__file__).parent / "flask_dashboard"
sys.path.insert(0, str(dashboard_dir))
sys.path.insert(0, str(Path(__file__).parent))

def start_frontend():
    """Start ONLY the Flask Dashboard"""
    try:
        # Change to flask_dashboard directory
        os.chdir(dashboard_dir)
        print(f"📁 Working directory: {Path.cwd()}")

        # Import Flask app
        from app.dashboard import create_app
        app = create_app()

        print("✅ Flask app imported successfully")
        print(f"🔗 API_BASE configured as: {os.getenv('API_BASE')}")

        # Get port from environment
        port = int(os.getenv("PORT", 8050))
        host = "0.0.0.0"
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

        print(f"🚀 Starting Flask Dashboard on {host}:{port}")
        print(f"🎯 This is the FRONTEND - NOT the API backend!")

        # Start Flask app
        app.run(
            host=host,
            port=port,
            debug=debug
        )

    except Exception as e:
        print(f"❌ Frontend startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_frontend()