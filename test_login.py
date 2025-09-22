#!/usr/bin/env python3
"""
Testar login no dashboard
"""
import requests

def test_login():
    """Testar login com usuário admin"""

    # URL base do dashboard
    base_url = "http://localhost:8050"

    # Dados de login do admin (como está no README)
    login_data = {
        'email': 'admin@transpontual.com',
        'password': 'admin123'
    }

    print("[LOGIN TEST] Testando login no dashboard...")

    # Criar sessão para manter cookies
    session = requests.Session()

    try:
        # 1. Tentar página de login
        login_page = session.get(f"{base_url}/login")
        print(f"[LOGIN PAGE] Status: {login_page.status_code}")

        # 2. Fazer login
        login_response = session.post(f"{base_url}/login", data=login_data)
        print(f"[LOGIN POST] Status: {login_response.status_code}")
        print(f"[LOGIN POST] Final URL: {login_response.url}")

        # 3. Tentar acessar página de veículos
        vehicles_page = session.get(f"{base_url}/vehicles")
        print(f"[VEHICLES PAGE] Status: {vehicles_page.status_code}")
        print(f"[VEHICLES PAGE] Final URL: {vehicles_page.url}")

        if vehicles_page.status_code == 200:
            print("[SUCCESS] Login funcionando e página de veículos acessível!")
        else:
            print("[ERROR] Problema no acesso após login")

    except Exception as e:
        print(f"[ERROR] Erro no teste: {e}")

if __name__ == "__main__":
    test_login()