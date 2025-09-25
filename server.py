#!/usr/bin/env python3
"""
Transpontual - Unified Server (Dashboard + API)
Runs Flask Dashboard with FastAPI proxy for API routes
"""
import os
import sys
from pathlib import Path
import threading
import time

def start_fastapi_backend():
    """Start FastAPI backend in background"""
    try:
        print("🔌 Starting FastAPI Backend...")

        # Add backend to path
        backend_dir = Path(__file__).parent / "backend_fastapi"
        sys.path.insert(0, str(backend_dir))

        # Import and start FastAPI
        from app.main import app
        import uvicorn

        # Run FastAPI on internal port
        uvicorn.run(app, host="127.0.0.1", port=8005, log_level="info")

    except Exception as e:
        print(f"❌ FastAPI Backend failed: {e}")

def start_flask_dashboard():
    """Start Flask Dashboard with API proxy"""
    try:
        print("🌐 Starting Flask Dashboard...")

        # Add dashboard to path
        dashboard_dir = Path(__file__).parent / "flask_dashboard"
        sys.path.insert(0, str(dashboard_dir))

        # Import Flask app (create_app is in app/dashboard.py)
        from app.dashboard import create_app
        app = create_app()

        # Configure API proxy (Flask Dashboard will proxy /api/* to FastAPI)
        port = int(os.getenv("PORT", 8080))
        host = "0.0.0.0"

        print(f"🚀 Starting Unified Server on {host}:{port}")
        print(f"📊 Dashboard: http://{host}:{port}/")
        print(f"🔌 API: http://{host}:{port}/api/*")

        # Start Flask Dashboard
        app.run(host=host, port=port, debug=False)

    except Exception as e:
        print(f"❌ Flask Dashboard failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Transpontual Unified Server Starting...")

    # Start FastAPI in background thread
    api_thread = threading.Thread(target=start_fastapi_backend, daemon=True)
    api_thread.start()

    # Wait a moment for FastAPI to start
    time.sleep(3)

    # Start Flask Dashboard (main thread)
    start_flask_dashboard()

