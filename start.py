#!/usr/bin/env python3
"""
Smart Auto-Detect Launcher
Automatically detects and starts the correct service based on environment and file structure
"""
import os
import sys
from pathlib import Path

def detect_and_start():
    """Auto-detect which service to start based on multiple factors"""

    print("🔍 SMART SERVICE DETECTION")
    print("=" * 50)

    # Debug: Print relevant environment variables
    railway_env = os.getenv('RAILWAY_ENVIRONMENT', 'unknown')
    railway_url = os.getenv('RAILWAY_STATIC_URL', 'unknown')
    railway_service = os.getenv('RAILWAY_SERVICE_NAME', 'unknown')
    print(f"Environment: {railway_env}")
    print(f"URL: {railway_url}")
    print(f"Service: {railway_service}")
    print("=" * 50)

    # Method 1: Check Railway URL FIRST (HIGHEST PRIORITY)
    railway_url = os.getenv('RAILWAY_STATIC_URL', '')
    if 'production-6938' in railway_url:
        print(f"🎯 Railway URL '{railway_url}' is production-6938 - FORCING FRONTEND")
        start_frontend()
        return
    elif 'production-256fe' in railway_url:
        print(f"🎯 Railway URL '{railway_url}' is production-256fe - FORCING BACKEND")
        start_backend()
        return

    # Method 2: Check environment variable
    service_type = os.getenv('SERVICE_TYPE', '').lower()
    if service_type:
        print(f"🎯 SERVICE_TYPE detected: {service_type}")
        if service_type == 'backend':
            start_backend()
            return
        elif service_type == 'frontend':
            start_frontend()
            return

    # Method 3: Check for service indicator files (LOWER PRIORITY)
    backend_indicator = Path("BACKEND_SERVICE")
    frontend_indicator = Path("FRONTEND_SERVICE")

    if backend_indicator.exists():
        print("🎯 BACKEND_SERVICE file detected - Starting FastAPI")
        start_backend()
        return

    if frontend_indicator.exists():
        print("🎯 FRONTEND_SERVICE file detected - Starting Flask Dashboard")
        start_frontend()
        return

    # Method 4: Check Railway service name pattern (fallback)
    service_name = os.getenv('RAILWAY_SERVICE_NAME', '').lower()
    if 'backend' in service_name or 'api' in service_name:
        print(f"🎯 Railway service name '{service_name}' suggests backend")
        start_backend()
        return
    elif 'frontend' in service_name or 'dashboard' in service_name:
        print(f"🎯 Railway service name '{service_name}' suggests frontend")
        start_frontend()
        return

    # Default: Start backend (FastAPI)
    print("🎯 No specific indicators found - defaulting to FastAPI backend")
    start_backend()

def start_backend():
    """Start FastAPI Backend"""
    print("🔧 STARTING FASTAPI BACKEND")
    print("=" * 50)

    try:
        backend_dir = Path(__file__).parent / "backend_fastapi"
        if not backend_dir.exists():
            raise Exception("backend_fastapi directory not found")

        sys.path.insert(0, str(backend_dir))
        os.chdir(backend_dir)
        print(f"Working directory: {Path.cwd()}")

        from app.main import app
        import uvicorn

        port = int(os.getenv("PORT", 8000))
        host = "0.0.0.0"

        print("FastAPI app imported successfully")
        print(f"Starting FastAPI Backend on {host}:{port}")
        print(f"API docs at: http://{host}:{port}/docs")

        uvicorn.run(app, host=host, port=port, log_level="info")

    except Exception as e:
        print(f"Backend startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def start_frontend():
    """Start Flask Dashboard Frontend"""
    print("🎨 STARTING FLASK DASHBOARD")
    print("=" * 50)

    try:
        # Configure API_BASE
        api_base_from_env = os.getenv('API_BASE')
        if not api_base_from_env:
            api_base = 'https://web-production-256fe.up.railway.app'
            os.environ.setdefault('API_BASE', api_base)
            print(f"API_BASE set to: {api_base}")

        os.environ.setdefault('FLASK_ENV', 'production')

        dashboard_dir = Path(__file__).parent / "flask_dashboard"
        sys.path.insert(0, str(dashboard_dir))
        os.chdir(dashboard_dir)

        print(f"Working directory: {Path.cwd()}")

        from app.dashboard import create_app
        app = create_app()

        port = int(os.getenv("PORT", 8050))
        host = "0.0.0.0"
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

        print("Flask app imported successfully")
        print(f"Starting Flask Dashboard on {host}:{port}")
        print(f"This is the FRONTEND Dashboard")

        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        print(f"Frontend startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    detect_and_start()