#!/usr/bin/env python3
"""
Universal App Launcher - Decides whether to run Frontend or Backend
Based on SERVICE_TYPE environment variable
"""
import os
import sys
from pathlib import Path

def main():
    service_type = os.getenv('SERVICE_TYPE', '').lower()

    print("🚀 UNIVERSAL APP LAUNCHER")
    print("=" * 50)
    print(f"SERVICE_TYPE: {service_type}")
    print("=" * 50)

    if service_type == 'backend':
        print("🔧 Starting FastAPI Backend...")
        start_backend()
    elif service_type == 'frontend':
        print("🎨 Starting Flask Frontend...")
        start_frontend()
    else:
        print("❌ SERVICE_TYPE not set or invalid!")
        print("Set SERVICE_TYPE to 'backend' or 'frontend'")
        sys.exit(1)

def start_backend():
    """Start FastAPI Backend"""
    try:
        # Change to backend directory
        backend_dir = Path(__file__).parent / "backend_fastapi"
        if not backend_dir.exists():
            raise Exception("backend_fastapi directory not found")

        os.chdir(backend_dir)
        print(f"📁 Changed to: {Path.cwd()}")

        # Import and run FastAPI
        from app.main import app
        import uvicorn

        port = int(os.getenv("PORT", 8000))
        print(f"🚀 Starting FastAPI on port {port}")

        uvicorn.run(app, host="0.0.0.0", port=port)

    except Exception as e:
        print(f"❌ Backend startup failed: {e}")
        sys.exit(1)

def start_frontend():
    """Start Flask Frontend"""
    try:
        # Configure API_BASE
        api_base_from_env = os.getenv('API_BASE')
        if not api_base_from_env:
            api_base = 'https://web-production-256fe.up.railway.app'
            os.environ.setdefault('API_BASE', api_base)
            print(f"🔗 API_BASE set to: {api_base}")

        os.environ.setdefault('FLASK_ENV', 'production')

        # Change to flask directory
        dashboard_dir = Path(__file__).parent / "flask_dashboard"
        sys.path.insert(0, str(dashboard_dir))
        os.chdir(dashboard_dir)

        print(f"📁 Changed to: {Path.cwd()}")

        # Import and run Flask
        from app.dashboard import create_app
        app = create_app()

        port = int(os.getenv("PORT", 8050))
        print(f"🎨 Starting Flask Dashboard on port {port}")

        app.run(host="0.0.0.0", port=port, debug=False)

    except Exception as e:
        print(f"❌ Frontend startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()