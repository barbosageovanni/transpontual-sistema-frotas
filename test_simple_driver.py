#!/usr/bin/env python3
"""
Teste simples de cadastro de motorista
"""
import requests
import json

def test_simple_driver():
    base_url = "http://localhost:8050"
    session = requests.Session()

    # Login
    login_data = {'email': 'admin@transpontual.com', 'password': 'admin123'}
    session.post(f"{base_url}/login", data=login_data)

    # Teste dados mais simples
    driver_data = {
        'nome': 'Motorista Simples',
        'cnh': '12345678901',
        'categoria': 'D',
        'ativo': True
    }

    headers = {'Content-Type': 'application/json'}

    response = session.post(
        f"{base_url}/drivers/new",
        data=json.dumps(driver_data),
        headers=headers
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_simple_driver()