#!/usr/bin/env python3
"""
Alternative entry point for Railway deployment
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Debug information
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {Path(__file__).resolve()}")
print(f"Python path: {sys.path}")

# List files in current directory
print("Files in current directory:")
for item in current_dir.iterdir():
    print(f"  {item}")

try:
    from app.main import app
    print("✅ Successfully imported app from app.main")

    if __name__ == "__main__":
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        print(f"🚀 Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Available modules in app directory:")
    app_dir = current_dir / "app"
    if app_dir.exists():
        for item in app_dir.iterdir():
            print(f"  {item}")
    else:
        print("  app directory not found!")

    # Try alternative import
    try:
        sys.path.insert(0, str(current_dir / "app"))
        import main as app_main
        app = app_main.app
        print("✅ Alternative import successful")

        if __name__ == "__main__":
            import uvicorn
            port = int(os.getenv("PORT", 8000))
            print(f"🚀 Starting server on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port)

    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        sys.exit(1)
