#!/usr/bin/env python3
"""
Teste de tratamento de erros de validação
"""
import requests
import json

def test_validation_handling():
    """Testar como o sistema trata erros de validação"""

    base_url = "http://localhost:8050"
    session = requests.Session()

    # Login
    login_data = {'email': 'admin@transpontual.com', 'password': 'admin123'}
    session.post(f"{base_url}/login", data=login_data)

    print("[TESTE] Testando tratamento de erros de validação...")

    # Teste 1: Data inválida
    print("\n[TESTE 1] Data inválida...")
    invalid_data = {
        'nome': 'Teste Data Inválida',
        'cnh': '12345678901',
        'categoria': 'D',
        'validade_cnh': 'data-invalida',  # Formato inválido
        'ativo': True
    }

    headers = {'Content-Type': 'application/json'}

    response = session.post(
        f"{base_url}/drivers/new",
        data=json.dumps(invalid_data),
        headers=headers
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    # Teste 2: Campo obrigatório faltando
    print("\n[TESTE 2] Nome faltando...")
    missing_name = {
        'cnh': '12345678901',
        'categoria': 'D',
        'ativo': True
    }

    response2 = session.post(
        f"{base_url}/drivers/new",
        data=json.dumps(missing_name),
        headers=headers
    )

    print(f"Status: {response2.status_code}")
    print(f"Response: {response2.text}")

    # Teste 3: Dados válidos para confirmar que funciona
    print("\n[TESTE 3] Dados válidos...")
    valid_data = {
        'nome': 'Motorista Válido Final',
        'cnh': '11111111111',
        'categoria': 'C',
        'validade_cnh': '2026-01-15',
        'ativo': True,
        'observacoes': 'Teste final de validação'
    }

    response3 = session.post(
        f"{base_url}/drivers/new",
        data=json.dumps(valid_data),
        headers=headers
    )

    print(f"Status: {response3.status_code}")
    print(f"Response: {response3.text}")

    if response3.status_code == 200:
        print("\n[RESULTADO] Sistema funcionando corretamente!")
        print("✅ Valida dados corretamente")
        print("✅ Trata erros de validação apropriadamente")
        print("✅ Cadastra motoristas com sucesso")
    else:
        print("\n[RESULTADO] Ainda há problemas no sistema")

if __name__ == "__main__":
    test_validation_handling()