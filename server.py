#!/usr/bin/env python3
"""
Railway deployment entry point - Flask Dashboard
"""
import os
import sys
from pathlib import Path

# Add flask_dashboard to Python path
dashboard_dir = Path(__file__).parent / "flask_dashboard"
sys.path.insert(0, str(dashboard_dir))
sys.path.insert(0, str(Path(__file__).parent))

def start_server():
    """Start the Flask Dashboard server"""
    try:
        # Change to flask_dashboard directory for imports
        os.chdir(dashboard_dir)

        # Import the Flask app
        from app.dashboard import create_app
        app = create_app()

        print("[OK] Flask app imported successfully from flask_dashboard")

        # Get port from environment (Railway sets PORT)
        port = int(os.getenv("PORT", 8050))
        host = "0.0.0.0"
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

        print(f"[INFO] Starting Flask server on {host}:{port}")
        print(f"[INFO] Working directory: {os.getcwd()}")
        print(f"[INFO] Debug mode: {debug}")

        # Start Flask app
        app.run(
            host=host,
            port=port,
            debug=debug
        )

    except ImportError as e:
        print(f"[ERROR] Failed to import Flask app: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        print("Files in current directory:")
        for item in Path.cwd().iterdir():
            print(f"  {item}")

        print("\nFiles in flask_dashboard:")
        if dashboard_dir.exists():
            for item in dashboard_dir.iterdir():
                print(f"  {item}")
        else:
            print("  flask_dashboard directory not found!")

        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_server()
