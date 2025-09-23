#!/usr/bin/env python3
"""
Teste básico para verificar se o container pode iniciar
"""
import os
import sys
import time

print("=== TESTE DE CONTAINER ===")
print(f"Python version: {sys.version}")
print(f"PORT env var: {os.getenv('PORT', 'NOT SET')}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

# Testar se conseguimos importar Flask
try:
    from flask import Flask
    print("✅ Flask import: OK")
except Exception as e:
    print(f"❌ Flask import error: {e}")
    sys.exit(1)

# Criar app Flask básica
try:
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Container funcionando!"

    print("✅ Flask app creation: OK")
except Exception as e:
    print(f"❌ Flask app creation error: {e}")
    sys.exit(1)

# Tentar iniciar na porta
try:
    port = int(os.getenv("PORT", "8050"))
    print(f"🚀 Starting on port {port}...")

    app.run(host="0.0.0.0", port=port, debug=False)
except Exception as e:
    print(f"❌ Flask run error: {e}")
    sys.exit(1)