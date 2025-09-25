#!/usr/bin/env python3
"""
Railway Backend Launcher - FORCES FastAPI ONLY
This script ONLY runs FastAPI Backend - no Flask allowed!
"""
import os
import sys
from pathlib import Path

def force_backend():
    """ABSOLUTELY FORCE FastAPI Backend - NO FLASK"""
    print("RAILWAY BACKEND LAUNCHER")
    print("FORCING FASTAPI BACKEND - NO FLASK ALLOWED!")
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
        print("THIS IS THE FASTAPI BACKEND")

        uvicorn.run(app, host=host, port=port, log_level="info")

    except Exception as e:
        print(f"Backend startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    force_backend()