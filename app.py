#!/usr/bin/env python3
"""
Transpontual - Application Entry Point for Gunicorn
This file exports the Flask application for Gunicorn deployment
"""
import os
import sys
from pathlib import Path

# Add project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Load environment variables
from dotenv import load_dotenv

env_file = project_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print("✓ .env file loaded")

render_env = project_dir / ".env.render"
if render_env.exists():
    load_dotenv(render_env, override=True)
    print("✓ .env.render file loaded")

# Set environment defaults for production
os.environ.setdefault('ENV', 'production')
os.environ.setdefault('DEBUG', 'false')
os.environ.setdefault('LOG_LEVEL', 'INFO')
os.environ.setdefault('FLASK_SECRET_KEY', 'render-production-secret-key-2025-supabase')

# Add dashboard to path
dashboard_dir = project_dir / "flask_dashboard"
sys.path.insert(0, str(dashboard_dir))

# Import and create Flask app
try:
    print("Importing Flask dashboard...")
    from app.dashboard import create_app

    # Create the Flask application
    app = create_app()

    # Add health check endpoint
    @app.route('/health')
    def health_check():
        return {
            "status": "healthy",
            "service": "transpontual-dashboard",
            "mode": "gunicorn"
        }, 200

    print("✓ Flask app created successfully!")
    print(f"✓ Template folder: {app.template_folder}")
    print(f"✓ Static folder: {app.static_folder}")

except Exception as e:
    print(f"✗ Error creating Flask app: {e}")
    import traceback
    traceback.print_exc()

    # Fallback: Create minimal Flask app
    from flask import Flask, jsonify

    app = Flask(__name__)

    @app.route('/')
    def home():
        return jsonify({
            "message": "Transpontual Dashboard - Minimal Mode",
            "status": "error",
            "error": str(e),
            "note": "Dashboard failed to load, minimal mode active"
        })

    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "unhealthy",
            "service": "transpontual-dashboard",
            "mode": "fallback",
            "error": str(e)
        }), 503

# Export for Gunicorn
# Usage: gunicorn app:app -w 4 -b 0.0.0.0:10000
if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
