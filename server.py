#!/usr/bin/env python3
"""
Transpontual - Unified Server (Dashboard + API)
Runs Flask Dashboard with FastAPI proxy for API routes
"""
import os
import sys
from pathlib import Path
import threading
import time

def start_fastapi_backend():
    """Start FastAPI backend in background"""
    try:
        print("API: Starting FastAPI Backend...")

        # Load environment variables - try multiple sources
        from dotenv import load_dotenv

        # Try .env first
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            print("SUCCESS: .env file loaded")

        # Try .railway-env for Railway deployment
        railway_env = Path(__file__).parent / ".railway-env"
        if railway_env.exists():
            load_dotenv(railway_env)
            print("SUCCESS: .railway-env file loaded")

        # Set environment variables for Render deployment
        if not os.getenv('DATABASE_URL'):
            print("⚠️ Setting DATABASE_URL from hardcoded value...")
            # IPv4-only connection strings for better compatibility
            db_options = [
                "postgresql://postgres:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require",
                "postgresql://postgres.lijtncazuwnbydeqtoyz:Mariaana953%407334@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require",
                "postgresql://postgres:Mariaana953%407334@db.lijtncazuwnbydeqtoyz.supabase.co:5432/postgres?sslmode=require&connect_timeout=10",
            ]
            os.environ['DATABASE_URL'] = db_options[0]  # Start with first option
            os.environ['DATABASE_BACKUP_URLS'] = '|'.join(db_options[1:])  # Store alternatives
            os.environ['JWT_SECRET'] = "kj9q-Xfby"  # Render JWT secret
            os.environ['ENV'] = "production"

        # Check database URL
        db_url = os.getenv('DATABASE_URL')
        print(f"🗄️ DATABASE_URL: {'Set' if db_url else 'Not set'}")
        if db_url:
            print(f"🗄️ Database host: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'unknown'}")

        # Add backend to path
        backend_dir = Path(__file__).parent / "backend_fastapi"
        sys.path.insert(0, str(backend_dir))

        # Import and start FastAPI
        from app.main import app
        import uvicorn

        # Run FastAPI on internal port
        uvicorn.run(app, host="127.0.0.1", port=8005, log_level="info")

    except Exception as e:
        print(f"ERROR: FastAPI Backend failed: {e}")

def start_flask_dashboard():
    """Start Flask Dashboard with API proxy"""
    try:
        print("Starting Flask Dashboard...")

        # Add dashboard to path
        dashboard_dir = Path(__file__).parent / "flask_dashboard"
        sys.path.insert(0, str(dashboard_dir))

        # Debug: Check what files exist
        print(f"DIR: Dashboard directory: {dashboard_dir}")
        print(f"DIR: Directory exists: {dashboard_dir.exists()}")

        if dashboard_dir.exists():
            print("FOLDER: Files in flask_dashboard:")
            for item in dashboard_dir.iterdir():
                print(f"  {item.name}")

            app_dir = dashboard_dir / "app"
            if app_dir.exists():
                print("FOLDER: Files in flask_dashboard/app:")
                for item in app_dir.iterdir():
                    print(f"  {item.name}")

        # Try importing dashboard
        dashboard_file = dashboard_dir / "app" / "dashboard.py"
        if dashboard_file.exists():
            print("SUCCESS: dashboard.py found, importing...")

            # Use importlib for dynamic import
            import importlib.util

            # Set working directory to flask_dashboard for proper imports
            original_cwd = os.getcwd()
            os.chdir(dashboard_dir)

            try:
                spec = importlib.util.spec_from_file_location("dashboard", dashboard_file)
                dashboard_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(dashboard_module)

                app = dashboard_module.create_app()
                print("SUCCESS: Dashboard app created successfully!")

                # Fix template folder path
                templates_path = dashboard_dir / "app" / "templates"
                static_path = dashboard_dir / "app" / "static"

                app.template_folder = str(templates_path)
                app.static_folder = str(static_path)

                print(f"DIR: Template folder: {app.template_folder}")
                print(f"DIR: Static folder: {app.static_folder}")

            finally:
                # Restore original working directory
                os.chdir(original_cwd)

            # Check templates directory
            templates_dir = dashboard_dir / "app" / "templates"
            if templates_dir.exists():
                print(f"FOLDER: Templates directory exists: {templates_dir}")
                errors_dir = templates_dir / "errors"
                if errors_dir.exists():
                    print("FOLDER: Errors templates directory exists")
                    for template in errors_dir.glob("*.html"):
                        print(f"  📄 {template.name}")
                else:
                    print("ERROR: Errors templates directory missing")
            else:
                print("ERROR: Templates directory missing")

            # Override error handlers with simple responses
            @app.errorhandler(404)
            def handle_404(e):
                return {"error": "Not Found", "status": 404}, 404

            @app.errorhandler(500)
            def handle_500(e):
                return {"error": "Internal Server Error", "status": 500}, 500
        else:
            print("ERROR: dashboard.py not found, using simple Flask app...")
            from flask import Flask, jsonify
            app = Flask(__name__)

            @app.route('/')
            def home():
                return jsonify({
                    "message": "Transpontual API Proxy",
                    "status": "running",
                    "dashboard": "dashboard.py not found"
                })

        # Configure API proxy (Flask Dashboard will proxy /api/* to FastAPI)
        port = int(os.getenv("PORT", 10000))  # Render default port
        host = "0.0.0.0"

        print(f"🚀 Starting Unified Server on {host}:{port}")
        print(f"📊 Dashboard: http://{host}:{port}/")
        print(f"API: API: http://{host}:{port}/api/*")

        # Start Flask Dashboard
        app.run(host=host, port=port, debug=False)

    except Exception as e:
        print(f"ERROR: Flask Dashboard failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Transpontual Unified Server Starting... [KEYERROR-FIX-ACTIVE]")
    print("🔧 EMERGENCY: KeyError fix applied - timestamp: 2025-09-26 11:30")

    # Start FastAPI in background thread
    api_thread = threading.Thread(target=start_fastapi_backend, daemon=True)
    api_thread.start()

    # Wait a moment for FastAPI to start
    time.sleep(3)

    # Start Flask Dashboard (main thread)
    start_flask_dashboard()

