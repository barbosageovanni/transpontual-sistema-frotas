#!/usr/bin/env python3
"""
BACKEND ONLY - Force FastAPI execution
"""
import os
import sys
from pathlib import Path

print("BACKEND API STARTUP")
print("=" * 60)
print("This script ONLY starts FastAPI Backend - NOT Flask Dashboard!")
print("=" * 60)

def start_backend():
    """Start ONLY the FastAPI Backend"""
    try:
        # Change to backend directory
        backend_dir = Path(__file__).parent / "backend_fastapi"
        if not backend_dir.exists():
            raise Exception("backend_fastapi directory not found")

        # Add to Python path
        sys.path.insert(0, str(backend_dir))
        os.chdir(backend_dir)
        print(f"Working directory: {Path.cwd()}")

        # Import FastAPI app and uvicorn
        from app.main import app
        import uvicorn

        # Get port from environment
        port = int(os.getenv("PORT", 8000))
        host = "0.0.0.0"

        print("FastAPI app imported successfully")
        print(f"Starting FastAPI Backend on {host}:{port}")
        print(f"This is the BACKEND API - NOT the frontend dashboard!")
        print(f"API docs will be available at: http://{host}:{port}/docs")

        # Start FastAPI with uvicorn
        uvicorn.run(app, host=host, port=port, log_level="info")

    except Exception as e:
        print(f"Backend startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_backend()