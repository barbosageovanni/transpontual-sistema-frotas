#!/usr/bin/env python3
"""
Universal server entry point - works with both Railway and local deployment
"""
import os
import sys
from pathlib import Path

# Add backend_fastapi directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Also add the parent directory (project root) to handle imports
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

def start_server():
    """Start the FastAPI server"""
    try:
        # Import the FastAPI app
        from app.main import app
        print("✅ FastAPI app imported successfully")

        # Start with uvicorn
        import uvicorn

        # Get port from environment (Railway sets PORT)
        port = int(os.getenv("PORT", 8000))
        host = "0.0.0.0"

        print(f"🚀 Starting server on {host}:{port}")
        print(f"🩺 Health check available at: http://{host}:{port}/health")

        # Configure uvicorn with health check optimization
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=5,
            timeout_graceful_shutdown=10
        )

    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        print("Files in current directory:")
        for item in Path.cwd().iterdir():
            print(f"  {item}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()