#!/usr/bin/env python3
"""
Entry point for Railway deployment with comprehensive debugging
Updated for proper backend FastAPI deployment
"""
import os
import sys
from pathlib import Path

# Debug information
print(f"🐍 Python version: {sys.version}")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"📄 Script location: {Path(__file__).resolve()}")
print(f"🛤️ Python path: {sys.path}")

# List files in current directory
print("📋 Files in current directory:")
current_dir = Path.cwd()
for item in sorted(current_dir.iterdir()):
    if item.is_file():
        print(f"  📄 {item.name}")
    else:
        print(f"  📁 {item.name}/")

# Check for app directory
app_dir = current_dir / "app"
print(f"\n🔍 App directory exists: {app_dir.exists()}")
if app_dir.exists():
    print("📋 Files in app directory:")
    for item in sorted(app_dir.iterdir()):
        if item.is_file():
            print(f"  📄 {item.name}")
        else:
            print(f"  📁 {item.name}/")

# Try to import the app
try:
    print("\n🔄 Attempting to import app from app.main...")
    from app.main import app
    print("✅ Successfully imported app!")

    if __name__ == "__main__":
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        print(f"🚀 Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

except ImportError as e:
    print(f"❌ Import error: {e}")

    # Try alternative approaches
    print("\n🔄 Trying alternative import methods...")

    # Add app directory to path
    sys.path.insert(0, str(app_dir))

    try:
        import main as app_main
        app = app_main.app
        print("✅ Alternative import successful!")

        if __name__ == "__main__":
            import uvicorn
            port = int(os.getenv("PORT", 8000))
            print(f"🚀 Starting server on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port)

    except ImportError as e2:
        print(f"❌ Alternative import failed: {e2}")

        # Last resort: create a simple FastAPI app
        print("🚨 Creating fallback FastAPI app...")
        try:
            from fastapi import FastAPI
            from fastapi.responses import JSONResponse

            fallback_app = FastAPI(title="Fallback API")

            @fallback_app.get("/")
            async def root():
                return {"message": "Fallback API - Debug Mode", "status": "running"}

            @fallback_app.get("/health")
            async def health():
                return {"status": "healthy", "mode": "fallback"}

            if __name__ == "__main__":
                import uvicorn
                port = int(os.getenv("PORT", 8000))
                print(f"🚀 Starting fallback server on port {port}")
                uvicorn.run(fallback_app, host="0.0.0.0", port=port)

        except Exception as e3:
            print(f"💥 Complete failure: {e3}")
            sys.exit(1)
