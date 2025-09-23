#!/usr/bin/env python3
"""
Aplicação Flask simplificada para teste
"""
import os
from flask import Flask

def create_simple_app():
    app = Flask(__name__)
    app.secret_key = "test-secret"

    @app.route('/')
    def hello():
        return '<h1>Flask Dashboard funcionando!</h1><p>Porta: {}</p>'.format(os.getenv("PORT", "8050"))

    @app.route('/health')
    def health():
        return {'status': 'ok', 'port': os.getenv("PORT", "8050")}

    return app

if __name__ == "__main__":
    app = create_simple_app()
    port = int(os.getenv("PORT", "8050"))

    print(f"=== INICIANDO FLASK APP SIMPLES ===")
    print(f"Porta: {port}")
    print(f"Host: 0.0.0.0")
    print("=====================================")

    app.run(host="0.0.0.0", port=port, debug=False)