#!/usr/bin/env python3
"""
Teste da funcionalidade de edição de veículos
"""
import requests

def test_vehicle_edit():
    """Testar edição de veículo no dashboard"""

    base_url = "http://localhost:8050"
    session = requests.Session()

    print("[TESTE] Testando edição de veículos...")

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

        # 2. Testar acesso à página de edição do veículo ID 4
        edit_url = f"{base_url}/vehicles/4/edit"
        edit_response = session.get(edit_url)

        print(f"[TESTE] Acessando: {edit_url}")
        print(f"[RESPOSTA] Status: {edit_response.status_code}")
        print(f"[RESPOSTA] URL final: {edit_response.url}")

        if edit_response.status_code == 200 and '/edit' in edit_response.url:
            print("[OK] Página de edição acessível")

            # Verificar se o formulário contém dados do veículo
            if 'ABC1234' in edit_response.text:  # Placa do veículo de teste
                print("[OK] Dados do veículo carregados no formulário")
            else:
                print("[AVISO] Dados do veículo não encontrados no formulário")

        elif 'vehicles' in edit_response.url and '/edit' not in edit_response.url:
            print("[ERRO] Redirecionado para listagem - veículo não encontrado")
        else:
            print(f"[ERRO] Problema no acesso à edição: {edit_response.status_code}")

        # 3. Testar outros veículos
        vehicle_ids = [5, 7, 8, 9]
        for vid in vehicle_ids:
            test_url = f"{base_url}/vehicles/{vid}/edit"
            test_response = session.get(test_url)
            status = "OK" if test_response.status_code == 200 and '/edit' in test_response.url else "ERRO"
            print(f"[TESTE] Veículo ID {vid}: {status}")

    except Exception as e:
        print(f"[ERRO] Erro durante teste: {e}")

if __name__ == "__main__":
    test_vehicle_edit()