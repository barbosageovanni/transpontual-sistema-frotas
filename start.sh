#!/bin/bash
echo "🚀 RAILWAY STARTUP SCRIPT"
echo "=========================="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Contents:"
ls -la

echo ""
echo "🔍 Looking for backend_fastapi directory..."
if [ -d "backend_fastapi" ]; then
    echo "✅ Found backend_fastapi directory"
    cd backend_fastapi
    echo "📁 Changed to: $(pwd)"
    echo "Contents:"
    ls -la

    echo ""
    echo "🐍 Installing dependencies..."
    pip install -r requirements.txt

    echo ""
    echo "🚀 Starting FastAPI server..."
    python server.py
else
    echo "❌ backend_fastapi directory not found!"
    echo "Available directories:"
    ls -la
    exit 1
fi