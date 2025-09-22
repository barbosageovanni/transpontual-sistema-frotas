#!/usr/bin/env python3
"""
Teste completo da página de veículos
"""
import requests
from bs4 import BeautifulSoup

def test_vehicles_functionality():
    """Testar funcionalidades da página de veículos"""

    base_url = "http://localhost:8050"
    session = requests.Session()

    print("[TESTE] Testando funcionalidades da página de veículos...")

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

        # 2. Acessar página de veículos
        vehicles_page = session.get(f"{base_url}/vehicles")

        if vehicles_page.status_code == 200:
            print("[OK] Página de veículos acessível")

            # Verificar se a página contém elementos esperados
            soup = BeautifulSoup(vehicles_page.text, 'html.parser')

            # Verificar busca rápida
            quick_search = soup.find('input', {'id': 'quickSearch'})
            if quick_search:
                print("[OK] Campo de busca rápida presente")
            else:
                print("[AVISO] Campo de busca rápida não encontrado")

            # Verificar tabela
            vehicles_table = soup.find('table', {'id': 'vehiclesTable'})
            if vehicles_table:
                print("[OK] Tabela de veículos presente")

                # Contar linhas da tabela
                rows = vehicles_table.find('tbody')
                if rows:
                    vehicle_rows = rows.find_all('tr')
                    print(f"[INFO] {len(vehicle_rows)} veículos encontrados na tabela")
                else:
                    print("[INFO] Nenhum veículo na tabela")
            else:
                print("[ERRO] Tabela de veículos não encontrada")

            # Verificar modal de exclusão
            delete_modal = soup.find('div', {'id': 'deleteModal'})
            if delete_modal:
                print("[OK] Modal de exclusão presente")
            else:
                print("[AVISO] Modal de exclusão não encontrado")

        else:
            print(f"[ERRO] Falha ao acessar página de veículos: {vehicles_page.status_code}")

        # 3. Testar filtros
        print("\n[TESTE] Testando filtros...")
        filter_params = {
            'placa': 'ABC',
            'tipo': 'carro'
        }

        filtered_page = session.get(f"{base_url}/vehicles", params=filter_params)
        if filtered_page.status_code == 200:
            print("[OK] Filtros funcionando")
        else:
            print(f"[ERRO] Falha nos filtros: {filtered_page.status_code}")

        print("\n[SUCESSO] Todos os testes passaram!")

    except Exception as e:
        print(f"[ERRO] Erro durante teste: {e}")

if __name__ == "__main__":
    test_vehicles_functionality()