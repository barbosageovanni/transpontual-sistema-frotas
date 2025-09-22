#!/usr/bin/env python3
"""
Teste completo de cadastro de motoristas
"""
import requests
import json

def test_driver_creation():
    """Testar cadastro de motorista no dashboard"""

    base_url = "http://localhost:8050"
    session = requests.Session()

    print("[TESTE] Testando cadastro de motoristas...")

    try:
        # 1. Fazer login
        login_data = {
            'email': 'admin@transpontual.com',
            'password': 'admin123'
        }

        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code != 200:
            print(f"[ERRO] Falha no login: {login_response.status_code}")
            return

        print("[OK] Login realizado com sucesso")

        # 2. Acessar página de cadastro
        new_driver_url = f"{base_url}/drivers/new"
        page_response = session.get(new_driver_url)

        if page_response.status_code == 200:
            print("[OK] Página de cadastro acessível")
        else:
            print(f"[ERRO] Erro ao acessar página: {page_response.status_code}")
            return

        # 3. Testar cadastro via AJAX (como o formulário faz)
        driver_data = {
            'nome': 'Motorista Teste Dashboard',
            'cnh': '12345678901',
            'categoria': 'D',
            'validade_cnh': '2025-12-31',
            'email': 'teste.motorista@dashboard.com',
            'senha': 'senha123',
            'ativo': True,
            'observacoes': 'Motorista cadastrado via teste'
        }

        headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }

        # POST via AJAX como o formulário faz
        create_response = session.post(
            new_driver_url,
            data=json.dumps(driver_data),
            headers=headers
        )

        print(f"[CADASTRO] Status: {create_response.status_code}")
        print(f"[CADASTRO] Response: {create_response.text[:200]}...")

        if create_response.status_code == 200:
            try:
                response_data = create_response.json()
                if 'message' in response_data:
                    print(f"[OK] {response_data['message']}")

                    # Verificar se foi realmente criado na API
                    api_check = requests.get("http://localhost:8005/api/v1/drivers")
                    if api_check.status_code == 200:
                        drivers = api_check.json()
                        test_driver = next((d for d in drivers if d.get('nome') == 'Motorista Teste Dashboard'), None)
                        if test_driver:
                            print(f"[VERIFICACAO] Motorista criado na API - ID: {test_driver.get('id')}")
                        else:
                            print("[AVISO] Motorista não encontrado na API")
                else:
                    print(f"[ERRO] Resposta inesperada: {response_data}")
            except json.JSONDecodeError:
                print("[ERRO] Resposta não é JSON válido")
        else:
            print(f"[ERRO] Falha no cadastro: {create_response.status_code}")

    except Exception as e:
        print(f"[ERRO] Erro durante teste: {e}")

if __name__ == "__main__":
    test_driver_creation()