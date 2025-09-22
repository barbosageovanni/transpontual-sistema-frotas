#!/usr/bin/env python3
"""
Teste completo de edição de veículo (visualização + atualização)
"""
import requests

def test_complete_vehicle_edit():
    """Teste completo de edição"""

    base_url = "http://localhost:8050"
    session = requests.Session()

    print("[TESTE] Teste completo de edição de veículo...")

    try:
        # Login
        login_data = {'email': 'admin@transpontual.com', 'password': 'admin123'}
        login_response = session.post(f"{base_url}/login", data=login_data)

        if login_response.status_code != 200:
            print(f"[ERRO] Falha no login")
            return

        print("[OK] Login realizado")

        # Testar edição do veículo ID 4
        vehicle_id = 4
        edit_url = f"{base_url}/vehicles/{vehicle_id}/edit"

        # 1. Acessar formulário de edição
        edit_get = session.get(edit_url)

        if edit_get.status_code == 200 and '/edit' in edit_get.url:
            print("[OK] Formulário de edição acessível")

            # 2. Simular envio de dados atualizados
            update_data = {
                'placa': 'ABC1234',  # Manter placa original
                'modelo': 'Test Car EDITADO',
                'ano': '2020',
                'km_atual': '55000',
                'ativo': 'on',
                'em_manutencao': 'on',
                'observacoes_manutencao': 'Teste de edição via dashboard'
            }

            # 3. Enviar atualização
            update_response = session.post(edit_url, data=update_data)

            print(f"[UPDATE] Status: {update_response.status_code}")
            print(f"[UPDATE] URL final: {update_response.url}")

            # Se redirecionou para a listagem, significa que deu certo
            if 'vehicles' in update_response.url and '/edit' not in update_response.url:
                print("[OK] Atualização bem-sucedida - redirecionado para listagem")

                # Verificar se os dados foram realmente atualizados via API
                api_check = requests.get(f"http://localhost:8005/api/v1/vehicles/{vehicle_id}")
                if api_check.status_code == 200:
                    vehicle_data = api_check.json()
                    print(f"[VERIFICACAO] Modelo: {vehicle_data.get('modelo')}")
                    print(f"[VERIFICACAO] KM: {vehicle_data.get('km_atual')}")
                    print(f"[VERIFICACAO] Em manutenção: {vehicle_data.get('em_manutencao')}")
                    print(f"[VERIFICACAO] Observações: {vehicle_data.get('observacoes_manutencao')}")
                else:
                    print("[ERRO] Não foi possível verificar os dados atualizados")
            else:
                print("[ERRO] Atualização falhou - não redirecionou corretamente")
        else:
            print("[ERRO] Não foi possível acessar o formulário de edição")

    except Exception as e:
        print(f"[ERRO] Erro durante teste: {e}")

if __name__ == "__main__":
    test_complete_vehicle_edit()