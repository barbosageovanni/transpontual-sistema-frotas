#!/usr/bin/env python3
"""
Railway deployment entry point - redirects to backend_fastapi
"""
import os
import sys
from pathlib import Path

# Add backend_fastapi to Python path
backend_dir = Path(__file__).parent / "backend_fastapi"
sys.path.insert(0, str(backend_dir))

# Change to backend directory
os.chdir(backend_dir)

def start_server():
    """Start the FastAPI server from backend_fastapi directory"""
    try:
        # Import the FastAPI app
        from app.main import app
        print("[OK] FastAPI app imported successfully from backend_fastapi")

        # Start with uvicorn
        import uvicorn

        # Get port from environment (Railway sets PORT)
        port = int(os.getenv("PORT", 8000))
        host = "0.0.0.0"

        print(f"[INFO] Starting server on {host}:{port}")
        print(f"[INFO] Working directory: {os.getcwd()}")

        # Configure uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )

    except ImportError as e:
        print(f"[ERROR] Failed to import app: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        print("Files in current directory:")
        for item in Path.cwd().iterdir():
            print(f"  {item}")

        print("\nFiles in backend_fastapi:")
        if backend_dir.exists():
            for item in backend_dir.iterdir():
                print(f"  {item}")
        else:
            print("  backend_fastapi directory not found!")

        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()