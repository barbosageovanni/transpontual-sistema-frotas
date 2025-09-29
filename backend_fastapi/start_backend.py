#!/usr/bin/env python3
"""
Force start FastAPI backend - ignores any Flask configuration
"""
import os
import sys
import subprocess
from pathlib import Path

print("🚀 FORCING FASTAPI BACKEND STARTUP")
print("=" * 50)

# Get current directory and ensure we're in the right place
current_dir = Path(__file__).parent
print(f"📁 Current script location: {current_dir}")
print(f"📁 Working directory: {Path.cwd()}")

# Change to backend_fastapi directory if needed
if current_dir.name == "backend_fastapi":
    os.chdir(current_dir)
    print(f"📁 Changed to: {Path.cwd()}")

# List what we have
print("\n📋 Files in current directory:")
for item in sorted(Path.cwd().iterdir()):
    print(f"  {'📁' if item.is_dir() else '📄'} {item.name}")

# Check if app directory exists
app_dir = Path.cwd() / "app"
if app_dir.exists():
    print(f"\n✅ App directory found: {app_dir}")
    print("📋 Contents:")
    for item in sorted(app_dir.iterdir()):
        print(f"  {'📁' if item.is_dir() else '📄'} {item.name}")
else:
    print(f"\n❌ App directory not found at: {app_dir}")
    sys.exit(1)

# Try to start FastAPI
try:
    print("\n🔥 STARTING FASTAPI WITH UVICORN")
    print("=" * 50)

    port = int(os.getenv("PORT", 8000))

    # Direct uvicorn command
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload" if os.getenv("FLASK_ENV") == "development" else "--no-reload"
    ]

    print(f"📝 Command: {' '.join(cmd)}")
    print(f"🌐 Will start on port: {port}")

    # Execute
    subprocess.run(cmd, check=True)

except Exception as e:
    print(f"💥 Failed to start FastAPI: {e}")
    print("\n🔄 Trying fallback method...")

    try:
        # Fallback - try main.py
        subprocess.run([sys.executable, "main.py"], check=True)
    except Exception as e2:
        print(f"💥 Fallback also failed: {e2}")
        sys.exit(1)
