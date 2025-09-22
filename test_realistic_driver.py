#!/usr/bin/env python3
"""
Teste realístico do formulário de motoristas
"""
import requests
import json

def test_realistic_driver_form():
    """Testar com dados que o formulário HTML real envia"""

    base_url = "http://localhost:8050"
    session = requests.Session()

    print("[TESTE] Simulando formulário real de motoristas...")

    try:
        # Login
        login_data = {'email': 'admin@transpontual.com', 'password': 'admin123'}
        session.post(f"{base_url}/login", data=login_data)

        # Dados como o formulário HTML envia
        form_data = {
            'nome': 'José Silva Santos',
            'cnh': '12345678901',
            'categoria': 'D',
            'validade_cnh': '2025-12-31',  # Formato HTML date input
            'email': 'jose.silva@teste.com',  # Campo que pode estar causando problema
            'senha': 'senha123456',  # Campo que pode estar causando problema
            'ativo': True,
            'observacoes': 'Motorista experiente'
        }

        headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }

        print(f"[ENVIO] Dados: {form_data}")

        response = session.post(
            f"{base_url}/drivers/new",
            data=json.dumps(form_data),
            headers=headers
        )

        print(f"[RESPOSTA] Status: {response.status_code}")
        print(f"[RESPOSTA] Headers: {dict(response.headers)}")
        print(f"[RESPOSTA] Body: {response.text}")

        if response.status_code == 200:
            print("[SUCESSO] Motorista cadastrado!")
        else:
            print(f"[ERRO] Falha no cadastro")

        # Teste 2: Sem campos problemáticos
        print("\n[TESTE 2] Sem email/senha...")
        form_data_simple = {
            'nome': 'Maria Santos',
            'cnh': '98765432101',
            'categoria': 'B',
            'validade_cnh': '2024-06-15',
            'ativo': True,
            'observacoes': 'Teste sem email/senha'
        }

        response2 = session.post(
            f"{base_url}/drivers/new",
            data=json.dumps(form_data_simple),
            headers=headers
        )

        print(f"[RESPOSTA 2] Status: {response2.status_code}")
        print(f"[RESPOSTA 2] Body: {response2.text}")

    except Exception as e:
        print(f"[ERRO] Erro durante teste: {e}")

if __name__ == "__main__":
    test_realistic_driver_form()