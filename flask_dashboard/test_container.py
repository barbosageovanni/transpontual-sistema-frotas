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
    port_env = os.getenv("PORT", "8050")
    print(f"Raw PORT env: '{port_env}'")

    # Tratar casos onde PORT pode estar vazio ou inválido
    if not port_env or port_env.strip() == "":
        port = 8050
        print("PORT empty, using default 8050")
    else:
        try:
            port = int(port_env.strip())
            print(f"PORT parsed successfully: {port}")
        except ValueError:
            port = 8050
            print(f"PORT invalid ('{port_env}'), using default 8050")

    print(f"🚀 Starting Flask on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
except Exception as e:
    print(f"❌ Flask run error: {e}")
    # Não fazer exit para manter container vivo e ver logs
    print("Container permanecerá vivo para debug...")
    import time
    time.sleep(3600)  # Sleep por 1 hora para debug