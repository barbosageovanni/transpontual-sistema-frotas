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

    print("SMART SERVICE DETECTION")
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
    railway_service = os.getenv('RAILWAY_SERVICE_NAME', '').lower()

    # ABSOLUTE PRIORITY: If this is production-6938, ONLY run Flask Dashboard
    if 'production-6938' in railway_url:
        print(f"DETECTED FRONTEND SERVICE: {railway_url}")
        print("FORCING FLASK DASHBOARD - NO FASTAPI ALLOWED!")
        start_frontend()
        return

    # Backend service
    elif 'production-256fe' in railway_url:
        print(f"DETECTED BACKEND SERVICE: {railway_url}")
        print("FORCING FASTAPI BACKEND - NO FLASK ALLOWED!")
        start_backend()
        return

    # Method 2: Check environment variable
    service_type = os.getenv('SERVICE_TYPE', '').lower()
    if service_type:
        print(f"SERVICE_TYPE detected: {service_type}")
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
        print("BACKEND_SERVICE file detected - Starting FastAPI")
        start_backend()
        return

    if frontend_indicator.exists():
        print("FRONTEND_SERVICE file detected - Starting Flask Dashboard")
        start_frontend()
        return

    # Method 4: Check Railway service name pattern (fallback)
    service_name = os.getenv('RAILWAY_SERVICE_NAME', '').lower()
    if 'backend' in service_name or 'api' in service_name:
        print(f"Railway service name '{service_name}' suggests backend")
        start_backend()
        return
    elif 'frontend' in service_name or 'dashboard' in service_name:
        print(f"Railway service name '{service_name}' suggests frontend")
        start_frontend()
        return

    # Default: Start backend (FastAPI)
    print("No specific indicators found - defaulting to FastAPI backend")
    start_backend()

def start_backend():
    """Start FastAPI Backend"""
    print("STARTING FASTAPI BACKEND")
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
    """Start Flask Dashboard Frontend - ABSOLUTELY NO FASTAPI"""
    print("STARTING FLASK DASHBOARD FRONTEND")
    print("THIS IS THE FRONTEND - NO FASTAPI SHOULD RUN")
    print("=" * 50)

    try:
        # Configure API_BASE to point to the backend service
        api_base_from_env = os.getenv('API_BASE')
        if not api_base_from_env:
            api_base = 'https://web-production-256fe.up.railway.app'
            os.environ['API_BASE'] = api_base
            print(f"✅ API_BASE configured: {api_base}")

        # Set Flask environment
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_APP'] = 'run.py'

        # Change to dashboard directory
        dashboard_dir = Path(__file__).parent / "flask_dashboard"
        if not dashboard_dir.exists():
            raise Exception(f"Flask dashboard directory not found: {dashboard_dir}")

        sys.path.insert(0, str(dashboard_dir))
        os.chdir(dashboard_dir)
        print(f"✅ Working directory: {Path.cwd()}")

        # Import Flask app directly
        print("🔄 Importing Flask Dashboard...")
        from run import app
        print("✅ Flask Dashboard imported successfully")

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
    detect_and_start()