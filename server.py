#!/usr/bin/env python3
"""
Railway deployment entry point - FORCED FASTAPI BACKEND
"""
import os
import sys
from pathlib import Path

print("FORCED BACKEND STARTUP - FASTAPI ONLY!")
print("=" * 60)

def start_server():
    """Start FASTAPI Backend - FORCED"""
    try:
        # Change to backend directory
        backend_dir = Path(__file__).parent / "backend_fastapi"
        if not backend_dir.exists():
            raise Exception("backend_fastapi directory not found")

        sys.path.insert(0, str(backend_dir))
        os.chdir(backend_dir)
        print(f"Working directory: {Path.cwd()}")

        # Import FastAPI app and uvicorn
        from app.main import app
        import uvicorn

        port = int(os.getenv("PORT", 8000))
        host = "0.0.0.0"

        print("FastAPI app imported successfully")
        print(f"Starting FORCED FastAPI Backend on {host}:{port}")
        print(f"API docs at: http://{host}:{port}/docs")

        # Start FastAPI
        uvicorn.run(app, host=host, port=port, log_level="info")

    except Exception as e:
        print(f"Backend startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_server()

