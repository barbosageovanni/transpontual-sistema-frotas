#!/usr/bin/env python3
"""
Railway Frontend Launcher - FORCES Flask Dashboard ONLY
This script ONLY runs Flask Dashboard - no FastAPI allowed!
"""
import os
import sys
from pathlib import Path

def force_frontend():
    """ABSOLUTELY FORCE Flask Dashboard - NO FASTAPI"""
    print("RAILWAY FRONTEND LAUNCHER")
    print("FORCING FLASK DASHBOARD - NO FASTAPI ALLOWED!")
    print("=" * 50)

    try:
        # Configure API_BASE to point to the backend service
        api_base = 'https://web-production-256fe.up.railway.app'
        os.environ['API_BASE'] = api_base
        print(f"API_BASE configured: {api_base}")

        # Set Flask environment
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_APP'] = 'run.py'

        # Change to dashboard directory
        dashboard_dir = Path(__file__).parent / "flask_dashboard"
        if not dashboard_dir.exists():
            raise Exception(f"Flask dashboard directory not found: {dashboard_dir}")

        sys.path.insert(0, str(dashboard_dir))
        os.chdir(dashboard_dir)
        print(f"Working directory: {Path.cwd()}")

        # Import Flask app directly
        print("Importing Flask Dashboard...")
        from run import app
        print("Flask Dashboard imported successfully")

        # Configure server
        port = int(os.getenv("PORT", 8050))
        host = "0.0.0.0"
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

        print(f"Starting Flask Dashboard Frontend")
        print(f"   Host: {host}:{port}")
        print(f"   Debug: {debug}")
        print(f"   Backend API: {os.getenv('API_BASE')}")
        print("THIS IS THE DASHBOARD FRONTEND")

        # Start Flask app
        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        print(f"Frontend startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    force_frontend()